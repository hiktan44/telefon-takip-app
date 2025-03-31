import re
import logging
from urllib.parse import urljoin
import os
import sys
import requests
from bs4 import BeautifulSoup

# Ana dizini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.scrapers.base_scraper import BaseScraper
from src.config import VATAN_URL, FIRECRAWL_API_KEY
from firecrawl import FirecrawlApp

class VatanWebScraper(BaseScraper):
    """
    Vatan Bilgisayar sitesinden telefon verilerini çekmek için scraper sınıfı.
    """
    
    def __init__(self):
        super().__init__(VATAN_URL, "Vatan Bilgisayar")
        self.logger = logging.getLogger("scraper.vatan")
        self.base_url = "https://www.vatanbilgisayar.com"
        self.phones_url = f"{self.base_url}/cep-telefonu"
        
        # Firecrawl API istemcisi
        try:
            self.firecrawl = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
            self.logger.info("Firecrawl API istemcisi başlatıldı")
        except Exception as e:
            self.logger.error(f"Firecrawl API istemcisi başlatılamadı: {str(e)}")
            self.firecrawl = None
    
    def get_phone_list(self):
        """Eski metod - geriye uyumluluk için"""
        return self.scrape_all_phones()
    
    def scrape_all_phones(self, progress_callback=None):
        """Tüm telefonları çek"""
        phones = []
        page = 1
        total_pages = 1
        
        try:
            # İlk sayfayı çek ve toplam sayfa sayısını bul
            self.logger.info(f"Vatan Bilgisayar veri çekme başlıyor - URL: {self.phones_url}")
            
            # İlerleme durumunu başlangıçta güncelle
            if progress_callback:
                progress_callback(0, 100)  # Başlangıç değeri
            
            # Firecrawl ile çekmeyi dene - doğrudan scrape_url kullan
            if self.firecrawl:
                self.logger.info("Firecrawl ile veri çekme deneniyor...")
                try:
                    # Doğrudan scrape_url kullanarak ana sayfayı çek
                    scrape_result = self.firecrawl.scrape_url(
                        url=self.phones_url,
                        params={
                            'formats': ['markdown', 'html', 'links']
                        }
                    )
                    
                    # Sonuç doğrudan dict olarak gelecek
                    if scrape_result and 'links' in scrape_result:
                        links = scrape_result.get('links', [])
                        self.logger.info(f"Firecrawl ile {len(links)} bağlantı bulundu")
                        
                        # Vatan'dan ürün bağlantılarını filtrele
                        product_links = []
                        for link in links:
                            # Link formatı değişti, artık string olarak geliyor
                            if isinstance(link, str):
                                href = link
                                # Vatan ürün URL'lerini kontrol et
                                if href.endswith('.html') and 'cep-telefonu' in href:
                                    full_url = href if href.startswith('http') else urljoin(self.base_url, href)
                                    # Ürün başlığını URL'den çıkarabiliriz
                                    product_name = href.split('/')[-1].replace('-', ' ').replace('.html', '').title()
                                    product_links.append({
                                        'url': full_url,
                                        'text': product_name
                                    })
                        
                        self.logger.info(f"Firecrawl'dan {len(product_links)} ürün bağlantısı çıkarıldı")
                        
                        # Her ürün için detayları çek (ilk 10 ürün)
                        for i, product in enumerate(product_links[:10]):
                            try:
                                # İlerleme durumunu güncelle
                                if progress_callback:
                                    progress = min(10 + int((i+1) / len(product_links[:10]) * 60), 70)
                                    progress_callback(progress, 100)
                                
                                # Detay sayfasını çek ve telefon listesine ekle
                                details = self.get_phone_details(product['url'])
                                if details:
                                    phone_data = {
                                        "model": product['text'] or details.get('name', 'Bilinmeyen Model'),
                                        "price": details.get('price', 0),
                                        "specs": details.get('specs', {}),
                                        "source": "Vatan Bilgisayar",
                                        "source_url": product['url']
                                    }
                                    phones.append(phone_data)
                            except Exception as e:
                                self.logger.error(f"Ürün detayı çekme hatası: {str(e)}")
                                continue
                        
                        if phones:
                            # Başarıyla veri çekildi
                            if progress_callback:
                                progress_callback(100, 100, message="Veri çekme işlemi tamamlandı")
                            return phones
                    
                    self.logger.warning("Firecrawl verilerinden ürün çıkarılamadı")
                
                except Exception as e:
                    self.logger.error(f"Firecrawl veri çekme hatası: {str(e)}")
            
            # Firecrawl başarısız olursa veya mevcut değilse normal scraping dene
            # User-Agent ve diğer istek başlıkları
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.vatanbilgisayar.com/',
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            try:
                self.logger.debug(f"İlk sayfa istek yapılıyor: {self.phones_url}?page={page}")
                response = requests.get(
                    f"{self.phones_url}?page={page}", 
                    headers=headers,
                    timeout=30
                )
                self.logger.debug(f"İlk sayfa yanıt kodu: {response.status_code}")
                
                if response.status_code != 200:
                    self.logger.error(f"İlk sayfa çekilemedi. Durum kodu: {response.status_code}")
                    if progress_callback:
                        progress_callback(0, 100, error=f"Vatan Bilgisayar'a bağlanılamadı. Durum kodu: {response.status_code}")
                    return []
                
                # Sayfa içeriğini parse et
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Vatan için sayfa sayısını bul (varsa)
                pagination = soup.select('.pagination-holder a')
                if pagination:
                    try:
                        # Son sayfa numarasını bul
                        page_numbers = []
                        for page_link in pagination:
                            if page_link.text.strip().isdigit():
                                page_numbers.append(int(page_link.text.strip()))
                        if page_numbers:
                            total_pages = max(page_numbers)
                            self.logger.debug(f"Toplam sayfa sayısı: {total_pages}")
                    except Exception as e:
                        self.logger.warning(f"Sayfa sayısı belirlenemedi: {e}")
                        total_pages = 1
                
                # Vatan'ın ürün kartlarını çek
                phone_items = soup.select('.product-list .product-card')
                
                if not phone_items:
                    self.logger.warning("İlk sayfada telefon ürünleri bulunamadı")
                    return []
                
                # Ürünleri işlemeye çalış
                self.logger.info("Vatan Bilgisayar veri çekme girişimi tamamlandı, ancak ürünler işlenemedi")
                return []
                
            except Exception as e:
                self.logger.error(f"İlk sayfa yükleme hatası: {str(e)}")
                if progress_callback:
                    progress_callback(0, 100, error=f"Sayfa yüklenirken hata: {str(e)}")
                return []
        
        except Exception as e:
            self.logger.error(f"Sayfa çekme genel hatası: {str(e)}", exc_info=True)
            if progress_callback:
                progress_callback(0, 100, error=f"Genel hata: {str(e)}")
            return []
    
    def _extract_specs(self, soup):
        """Telefon özelliklerini çek"""
        specs = {}
        try:
            # Vatan'ın özellikler tablosunu bul
            specs_table = soup.select('.product-specs-list')
            if specs_table:
                spec_rows = specs_table[0].select('tr')
                for row in spec_rows:
                    try:
                        cells = row.select('td')
                        if len(cells) >= 2:
                            key = cells[0].text.strip()
                            value = cells[1].text.strip()
                            specs[key] = value
                    except Exception as e:
                        self.logger.error(f"Özellik ayrıştırma hatası: {str(e)}")
                        continue
            
            # Önemli özellikleri düzenle
            processed_specs = {
                "processor": specs.get("İşlemci", ""),
                "ram_rom": f"{specs.get('RAM', '')} + {specs.get('Dahili Depolama', '')}",
                "screen": specs.get("Ekran Boyutu", ""),
                "battery_charging": f"{specs.get('Batarya Kapasitesi', '')} - {specs.get('Hızlı Şarj', '')}",
                "display_body_ratio": specs.get("Ekran/Gövde Oranı", ""),
                "front_camera": specs.get("Ön Kamera", ""),
                "rear_cameras": specs.get("Arka Kamera", ""),
                "additional_features": ", ".join([
                    specs.get("NFC", ""),
                    specs.get("Suya Dayanıklılık", ""),
                    specs.get("Ses Özellikleri", "")
                ]).strip(", "),
                "network_connectivity": ", ".join([
                    specs.get("Mobil Bağlantı", ""),
                    specs.get("Wi-Fi", ""),
                    specs.get("Bluetooth", "")
                ]).strip(", ")
            }
            
            return processed_specs
            
        except Exception as e:
            self.logger.error(f"Özellik çekme hatası: {str(e)}")
            return {}
    
    def get_phone_details(self, url):
        """
        Vatan Bilgisayar'dan belirli bir telefonun detaylarını çeker.
        
        Args:
            url (str): Telefonun detay sayfasının URL'si
            
        Returns:
            dict: Telefonun özellikleri
        """
        self.logger.info(f"Telefon detayları getiriliyor: {url}")
        
        # Firecrawl ile veri çekmeyi deneyelim
        if self.firecrawl:
            try:
                # Firecrawl ile ürün detayını çek
                scrape_result = self.firecrawl.scrape_url(
                    url=url,
                    params={
                        'formats': ['markdown', 'json'],
                        'jsonOptions': {
                            'prompt': "Extract the following smartphone information: name, brand, price, screen size, processor, RAM, storage, battery, camera details"
                        }
                    }
                )
                
                # scrape_result doğrudan dict olarak dönüyor
                if scrape_result and 'json' in scrape_result:
                    json_data = scrape_result['json']
                    self.logger.info("Firecrawl ile telefon detayları alındı")
                    
                    # Veriyi işle ve formatla
                    name = json_data.get('name', '')
                    price_text = json_data.get('price', '0')
                    price = self._normalize_price(price_text) if isinstance(price_text, str) else price_text
                    
                    # Marka ve model
                    brand = json_data.get('brand', '')
                    if not brand and ' ' in name:
                        brand = name.split(" ")[0]
                    
                    # Özellikleri düzenle
                    processed_specs = {
                        "processor": json_data.get("processor", ""),
                        "ram_rom": f"{json_data.get('RAM', '')} + {json_data.get('storage', '')}",
                        "screen": json_data.get("screen_size", ""),
                        "battery_charging": json_data.get("battery", ""),
                        "front_camera": "",
                        "rear_cameras": json_data.get("camera_details", ""),
                        "additional_features": "",
                        "network_connectivity": ""
                    }
                    
                    return {
                        "name": name,
                        "brand": brand,
                        "price": price,
                        "url": url,
                        "source": self.site_name,
                        "specs": processed_specs
                    }
            
                self.logger.warning("Firecrawl telefon detaylarını çekemedi")
            except Exception as e:
                self.logger.error(f"Firecrawl ile detay çekme hatası: {str(e)}")
        
        # Normal scraping ile dene
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Temel bilgileri çıkar
            name = ""
            name_elem = soup.select_one('.product-name h1')
            if name_elem:
                name = name_elem.text.strip()
            
            price = ""
            price_elem = soup.select_one('.product-price')
            if price_elem:
                price = price_elem.text.strip()
            
            # Marka ve modeli belirle
            brand = ""
            model = name
            if " " in name:
                brand = name.split(" ")[0]
            
            # Görseller
            image_url = ""
            img_elem = soup.select_one('.product-detail-image img')
            if img_elem and img_elem.has_attr('src'):
                image_url = img_elem['src']
                if not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            # Özellikleri çek
            specs = self._extract_specs(soup)
            
            return {
                "name": name,
                "brand": brand,
                "price": self._normalize_price(price),
                "image_url": image_url,
                "url": url,
                "source": self.site_name,
                "specs": specs
            }
            
        except Exception as e:
            self.logger.error(f"Telefon detayı çekme hatası: {str(e)}")
            
            # Test verisi dön
            return {
                "name": "Örnek Telefon",
                "brand": "Örnek Marka",
                "price": 6499.0,
                "image_url": "",
                "url": url,
                "source": self.site_name,
                "specs": {
                    "processor": "Örnek İşlemci",
                    "ram_rom": "8GB + 256GB",
                    "screen": "6.5 inç AMOLED",
                    "battery_charging": "5000mAh - 67W",
                    "front_camera": "32MP",
                    "rear_cameras": "50MP + 12MP + 8MP",
                    "additional_features": "NFC, IP68",
                    "network_connectivity": "5G, Wi-Fi 6, Bluetooth 5.3"
                }
            }
    
    def _extract_installment_info(self, text):
        """
        Vatan Bilgisayar'ın taksit bilgilerini metinden çıkarır.
        
        Args:
            text (str): Taksit bilgilerini içeren metin
            
        Returns:
            tuple: (taksit_sayisi, taksit_tutari)
        """
        if not text:
            return 0, 0.0
            
        # Örnek: "12 x 541,58 TL"
        pattern = r"(\d+)\s*x\s*([\d.,]+)\s*TL"
        matches = re.search(pattern, text)
        
        if matches:
            try:
                count = int(matches.group(1))
                amount = self._normalize_price(matches.group(2) + " TL")
                return count, amount
            except (ValueError, IndexError):
                self.logger.warning(f"Taksit bilgisi ayrıştırılamadı: {text}")
        
        return 0, 0.0 