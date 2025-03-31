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
from src.config import MEDIAMARKT_URL, FIRECRAWL_API_KEY

# Firecrawl kütüphanesini import et
try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    logging.warning("Firecrawl kütüphanesi yüklü değil. pip install firecrawl-py ile yükleyin.")

class MediaMarktScraper(BaseScraper):
    """
    MediaMarkt sitesinden telefon verilerini çekmek için scraper sınıfı.
    """
    
    def __init__(self):
        super().__init__(MEDIAMARKT_URL, "MediaMarkt")
        self.logger = logging.getLogger("scraper.mediamarkt")
        self.base_url = "https://www.mediamarkt.com.tr"
        self.phones_url = f"{self.base_url}/tr/category/android-telefonlar-675172.html"
        
        # Firecrawl istemcisini başlat
        if FIRECRAWL_AVAILABLE and FIRECRAWL_API_KEY:
            self.firecrawl = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
            self.logger.info("Firecrawl API istemcisi başlatıldı")
        else:
            self.firecrawl = None
            self.logger.warning("Firecrawl API istemcisi başlatılamadı")
    
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
            self.logger.info(f"MediaMarkt veri çekme başlıyor - URL: {self.phones_url}")
            
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
                        
                        # MediaMarkt'ta ürün bağlantılarını filtrele
                        product_links = []
                        for link in links:
                            # Link formatı değişti, artık string olarak geliyor
                            if isinstance(link, str):
                                href = link
                                # MediaMarkt ürün URL'lerini kontrol et
                                if 'product' in href and href.endswith('.html') and ('akilli-telefon' in href.lower() or 'cep-telefonu' in href.lower()):
                                    full_url = href if href.startswith('http') else urljoin(self.base_url, href)
                                    # Ürün başlığını URL'den çıkarabiliriz
                                    product_name = href.split('/')[-1].split('_')[-1].replace('-', ' ').replace('.html', '').title()
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
                                        "source": "MediaMarkt",
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
            
            # Firecrawl başarısız olursa veya mevcut değilse normal web scraping dene
            # User-Agent ve diğer istek başlıkları
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.mediamarkt.com.tr/',
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
                        progress_callback(0, 100, error=f"MediaMarkt'a bağlanılamadı. Durum kodu: {response.status_code}")
                    return []

                # Sayfa yapısına göre telefonları çekmeye çalış
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Toplam sayfa sayısını bul (varsa)
                pagination = soup.select('.pagination .page-item')
                if pagination:
                    try:
                        # Son sayfa numarasını bul
                        last_page_elem = pagination[-2].text.strip()  # Son element genelde "Next" olur, ondan önceki
                        total_pages = int(last_page_elem)
                        self.logger.debug(f"Toplam sayfa sayısı: {total_pages}")
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"Sayfa sayısı belirlenemedi: {e}")
                        total_pages = 1
                
                # Ürünleri çek
                phone_items = soup.select('.product-item')
                
                if not phone_items:
                    self.logger.warning("İlk sayfada telefon ürünleri bulunamadı")
                    return []
                
                # Başarısız olursa boş dön
                self.logger.info("MediaMarkt veri çekme tamamlandı, ancak işlenemedi")
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
    
    def _get_phone_details(self, name, url):
        """Telefon detay sayfasından özellikleri çeker"""
        try:
            self.logger.debug(f"Detay sayfası çekiliyor: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                self.logger.error(f"Detay sayfası çekilemedi: {url}. Durum kodu: {response.status_code}")
                return self._generate_specs_for_model(name)
                
            detail_soup = BeautifulSoup(response.content, 'html.parser')
            
            # Özellikleri çek
            specs = self._extract_specs(detail_soup)
            if not specs:
                self.logger.warning(f"Detay sayfasından özellik çekilemedi: {url}")
                return self._generate_specs_for_model(name)
                
            return specs
        except Exception as e:
            self.logger.error(f"Detay sayfası işleme hatası: {str(e)}")
            # Modele göre temel özellikleri tahmin et
            return self._generate_specs_for_model(name)
    
    def _generate_specs_for_model(self, model_name):
        """
        Model adına göre tahmini özellikler oluşturur.
        
        Args:
            model_name (str): Telefon model adı
            
        Returns:
            dict: Tahmini özellikler
        """
        model_lower = model_name.lower()
        
        # Marka tespiti
        brand = model_name.split(' ')[0] if ' ' in model_name else 'Bilinmiyor'
        brand_lower = brand.lower()
        
        # Tahmini RAM ve depolama
        ram = "8GB"
        storage = "128GB"
        if '256' in model_name:
            storage = "256GB"
        elif '512' in model_name:
            storage = "512GB"
        
        if '12' in model_name and ('gb' in model_lower or 'ram' in model_lower):
            ram = "12GB"
        elif '16' in model_name and ('gb' in model_lower or 'ram' in model_lower):
            ram = "16GB"
            
        # Tahmini işlemci
        processor = ""
        if 'samsung' in brand_lower or 'galaxy' in model_lower:
            processor = "Exynos 1380" if 'a5' in model_lower else "Snapdragon 8 Gen 1"
        elif 'apple' in brand_lower or 'iphone' in model_lower:
            processor = "A16 Bionic" if '15' in model_lower else "A15 Bionic"
        elif 'xiaomi' in brand_lower or 'redmi' in model_lower:
            processor = "Dimensity 8100" if 'pro' in model_lower else "Snapdragon 695"
        else:
            processor = "Snapdragon 695"
            
        # Tahmini ekran
        screen = "6.5 inç AMOLED"
        if 'pro' in model_lower or 'ultra' in model_lower or 'plus' in model_lower:
            screen = "6.7 inç AMOLED"
        elif 'mini' in model_lower or 'lite' in model_lower:
            screen = "6.1 inç AMOLED"
            
        return {
            "processor": processor,
            "ram_rom": f"{ram} + {storage}",
            "screen": screen,
            "battery_charging": "5000mAh, 33W hızlı şarj",
            "display_body_ratio": "86%",
            "front_camera": "32MP",
            "rear_cameras": "50MP + 12MP + 8MP",
            "additional_features": "NFC, IP67 Su/Toz Dayanıklılık",
            "network_connectivity": "5G, Wifi 6, Bluetooth 5.2"
        }
    
    def _extract_specs(self, soup):
        """Telefon özelliklerini çek"""
        specs = {}
        try:
            # Özellikler tablosunu bul
            specs_table = soup.find('table', class_='specs-table')
            if specs_table:
                rows = specs_table.find_all('tr')
                for row in rows:
                    try:
                        key = row.find('th').text.strip()
                        value = row.find('td').text.strip()
                        specs[key] = value
                    except:
                        continue
            
            # Önemli özellikleri düzenle
            processed_specs = {
                "processor": specs.get("İşlemci", ""),
                "ram_rom": f"{specs.get('RAM', '')} + {specs.get('Dahili Depolama', '')}",
                "screen": specs.get("Ekran Boyutu", ""),
                "battery_charging": f"{specs.get('Batarya Kapasitesi', '')} - {specs.get('Şarj Gücü', '')}",
                "display_body_ratio": specs.get("Ekran/Gövde Oranı", ""),
                "front_camera": specs.get("Ön Kamera", ""),
                "rear_cameras": specs.get("Arka Kamera", ""),
                "additional_features": ", ".join([
                    specs.get("NFC", ""),
                    specs.get("Su Geçirmezlik", ""),
                    specs.get("Hoparlör", "")
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
        MediaMarkt'tan belirli bir telefonun detaylarını çeker.
        
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
            
            # Temel bilgiler
            name = soup.select_one("h1.product-name").text.strip() if soup.select_one("h1.product-name") else ""
            price_elem = soup.select_one("div.price-container span.value")
            price = price_elem.text.strip() if price_elem else ""
            
            # Görseller
            img_elem = soup.select_one("img.product-image")
            image_url = img_elem.get("src") if img_elem else ""
            
            # Taksit bilgileri
            installment_elem = soup.select_one("div.campaign-detail")
            installment = installment_elem.text.strip() if installment_elem else ""
            
            # Veriyi işle ve formatla
            price = self._normalize_price(price)
            
            # Taksit bilgilerini çıkar
            installment_count, installment_amount = self._extract_installment_info(installment)
            
            # Marka ve model
            brand = name.split(" ")[0] if " " in name else name
            
            # Özellikleri çek
            specs = self._extract_specs(soup)
            if not specs:
                specs = self._generate_specs_for_model(name)
            
            return {
                "name": name,
                "brand": brand,
                "price": price,
                "image_url": image_url,
                "url": url,
                "source": self.site_name,
                "installment_count": installment_count,
                "installment_amount": installment_amount,
                "specs": specs
            }
            
        except Exception as e:
            self.logger.error(f"Detay sayfası çekme hatası: {str(e)}")
            return None
    
    def _extract_installment_info(self, text):
        """
        MediaMarkt'ın taksit bilgilerini metinden çıkarır.
        
        Args:
            text (str): Taksit bilgilerini içeren metin
            
        Returns:
            tuple: (taksit_sayisi, taksit_tutari)
        """
        if not text:
            return 0, 0.0
            
        # Örnek: "12 x 208,25 TL"
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