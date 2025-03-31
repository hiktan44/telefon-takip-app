import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import os
import sys

# Ana dizini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import FIRECRAWL_API_KEY

class BaseScraper(ABC):
    """
    Telefon verilerini çekmek için temel scraper sınıfı.
    Tüm site-spesifik scraperlar bu sınıftan türetilmelidir.
    """
    
    def __init__(self, base_url, site_name):
        self.base_url = base_url
        self.site_name = site_name
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        self.session = requests.Session()
        self.logger = logging.getLogger(f"scraper.{site_name}")
    
    def _get_page_content(self, url):
        """
        Belirtilen URL'den sayfa içeriğini alır.
        
        Args:
            url (str): İçeriği alınacak URL
            
        Returns:
            BeautifulSoup: Sayfa içeriğinin BeautifulSoup nesnesi
        """
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            self.logger.error(f"URL çekilirken hata oluştu {url}: {e}")
            return None
    
    def _get_page_with_selenium(self, url):
        """
        Selenium kullanarak JavaScript gerektiren sayfaları çeker.
        
        Args:
            url (str): İçeriği alınacak URL
            
        Returns:
            BeautifulSoup: Sayfa içeriğinin BeautifulSoup nesnesi
        """
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.get(url)
            time.sleep(3)  # Sayfanın yüklenmesi için bekle
            
            page_source = driver.page_source
            driver.quit()
            
            return BeautifulSoup(page_source, 'html.parser')
        except Exception as e:
            self.logger.error(f"Selenium ile sayfa çekilirken hata oluştu {url}: {e}")
            return None
    
    def _use_firecrawl(self, url, selectors):
        """
        Firecrawl API kullanarak veri çekme
        
        Args:
            url (str): Taranacak URL
            selectors (dict): CSS seçicilerinin sözlüğü
            
        Returns:
            dict: Çekilen veriler
        """
        if not FIRECRAWL_API_KEY:
            self.logger.error("Firecrawl API anahtarı tanımlanmamış")
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {FIRECRAWL_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "url": url,
                "waitFor": selectors.get("waitFor", "body"),
                "extract": selectors.get("extract", {})
            }
            
            response = requests.post(
                "https://api.firecrawl.dev/scrape",
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("data", {})
        except Exception as e:
            self.logger.error(f"Firecrawl ile veri çekilirken hata oluştu: {e}")
            return None
    
    def _normalize_price(self, price_text):
        """
        Fiyat metinlerini normalleştirir ve sayısal değere dönüştürür.
        
        Args:
            price_text (str): Fiyat metni (örn. "2.499,00 TL")
            
        Returns:
            float: Normalleştirilmiş fiyat değeri
        """
        if not price_text:
            return 0.0
            
        # Metni temizle
        price_text = price_text.replace("TL", "").replace("₺", "").strip()
        price_text = price_text.replace(".", "").replace(",", ".")
        
        try:
            return float(price_text)
        except ValueError:
            self.logger.warning(f"Fiyat dönüştürülemedi: {price_text}")
            return 0.0
    
    def _extract_installment_info(self, text):
        """
        Taksit bilgilerini metinden çıkarır.
        
        Args:
            text (str): Taksit bilgilerini içeren metin
            
        Returns:
            tuple: (taksit_sayisi, taksit_tutari)
        """
        # Bu metod alt sınıflarda site-spesifik olarak uygulanmalıdır
        return 0, 0.0
    
    @abstractmethod
    def get_phone_list(self):
        """
        Telefon listesini çeker.
        
        Returns:
            list: Telefon nesnelerinin listesi
        """
        pass
    
    @abstractmethod
    def get_phone_details(self, url):
        """
        Belirli bir telefonun detaylarını çeker.
        
        Args:
            url (str): Telefonun detay sayfasının URL'si
            
        Returns:
            dict: Telefonun özellikleri
        """
        pass 