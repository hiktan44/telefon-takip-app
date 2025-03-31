#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging

# Ana dizini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firecrawl import FirecrawlApp
from config import FIRECRAWL_API_KEY

# Logging yapılandırması
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_firecrawl():
    """Firecrawl API'sini test eder"""
    try:
        logger.info(f"Firecrawl API testi başlatılıyor. API key: {FIRECRAWL_API_KEY}")
        
        # Firecrawl istemcisini oluştur
        firecrawl = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        
        # Test URL'si
        test_url = "https://www.vatanbilgisayar.com/cep-telefonu"
        
        logger.info(f"API isteği yapılıyor: {test_url}")
        
        # scrape_url metodunu kullanarak direkt olarak sayfayı çek
        result = firecrawl.scrape_url(
            url=test_url,
            params={
                'formats': ['markdown', 'html', 'links']
            }
        )
        
        # Sonucu incele
        if result:
            logger.info("API isteği başarılı! Sonuç özeti:")
            
            # Dönen veri türlerini kontrol et
            for key in result.keys():
                if key == 'links' and isinstance(result[key], list):
                    logger.info(f"- Links: {len(result[key])} adet bağlantı bulundu")
                    
                    # İlk 5 bağlantıyı göster
                    for i, link in enumerate(result[key][:5]):
                        # Farklı link formatlarını kontrol et
                        if isinstance(link, dict):
                            href = link.get('href', 'Yok')
                            text = link.get('text', 'Yok')
                            logger.info(f"  {i+1}. Bağlantı (dict): {text} - {href}")
                        elif isinstance(link, str):
                            logger.info(f"  {i+1}. Bağlantı (str): {link}")
                        else:
                            logger.info(f"  {i+1}. Bağlantı (bilinmeyen format): {type(link)} - {link}")
                else:
                    content_type = type(result[key])
                    content_length = len(str(result[key]))
                    logger.info(f"- {key}: {content_type} - {content_length} karakter")
        else:
            logger.error("API yanıt vermedi veya boş yanıt döndü")
            
    except Exception as e:
        logger.error(f"Firecrawl API test hatası: {str(e)}", exc_info=True)

if __name__ == "__main__":
    logger.info("Firecrawl test uygulaması başladı")
    test_firecrawl()
    logger.info("Firecrawl test uygulaması tamamlandı") 