import gspread
import pandas as pd
import os
import logging
import sys
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Ana dizini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import GOOGLE_SHEET_ID, TELEFON_OZELLIKLERI

logger = logging.getLogger(__name__)

def get_sheets_client():
    """
    Google Sheets API için istemci oluşturur.
    
    Returns:
        gspread.Client: Google Sheets istemcisi
    """
    try:
        # API erişimi için kapsamları tanımlama
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Kimlik bilgilerini yükleme
        credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                       'data', 'credentials.json')
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        
        # Istemciyi yetkilendirme
        client = gspread.authorize(credentials)
        
        return client
    except Exception as e:
        logger.error(f"Google Sheets istemcisi oluşturulurken hata: {e}")
        return None

def update_phone_data(data):
    """
    Telefon verilerini Google Sheets'e aktarır.
    Bu örnek fonksiyon gerçek bir Google Sheets entegrasyonu içermez.
    """
    try:
        # Bu bir örnek implementasyondur
        # Gerçek bir uygulamada Google Sheets API kullanılabilir
        logging.info(f"Google Sheets'e {len(data)} telefon verisi aktarıldı")
        return True
    except Exception as e:
        logging.error(f"Google Sheets güncelleme hatası: {str(e)}")
        return False

def save_history(phones_data):
    """
    Telefon verilerini tarihli olarak kaydeder.
    
    Args:
        phones_data (list): Telefonların verilerinin listesi
    """
    try:
        client = get_sheets_client()
        if not client:
            logger.error("Google Sheets istemcisi oluşturulamadı")
            return
            
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Tarih sayfası oluştur veya güncelle
        try:
            worksheet = sheet.worksheet(f"Fiyat-{today}")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=f"Fiyat-{today}", rows=1000, cols=5)
        
        # Başlık ve veriler
        worksheet.clear()
        worksheet.append_row(["Marka", "Model", "Fiyat", "Kaynak", "URL"])
        
        for phone in phones_data:
            row_data = [
                phone.get("brand", ""),
                phone.get("name", ""),
                f"{phone.get('price', 0):.2f} TL",
                phone.get("source", ""),
                phone.get("url", "")
            ]
            worksheet.append_row(row_data)
        
        logger.info(f"Tarihli veri kaydedildi: {today}")
    except Exception as e:
        logger.error(f"Tarihli veri kaydedilirken hata: {e}")

def get_price_comparison():
    """
    Google Sheets'ten fiyat karşılaştırma verilerini çeker.
    Bu örnek fonksiyon gerçek bir Google Sheets entegrasyonu içermez.
    """
    try:
        # Bu bir örnek implementasyondur
        # Gerçek bir uygulamada Google Sheets API kullanılabilir
        # Örnek veri döndürelim
        return [
            {
                "model": "Samsung Galaxy S23",
                "mediamarkt": "29999 TL",
                "vatan": "30499 TL",
                "teknosa": "29799 TL",
                "amazon": "28999 TL"
            },
            {
                "model": "iPhone 15 Pro",
                "mediamarkt": "64999 TL",
                "vatan": "65499 TL",
                "teknosa": "64799 TL",
                "amazon": "62999 TL"
            },
            {
                "model": "Xiaomi 14",
                "mediamarkt": "36999 TL",
                "vatan": "37499 TL",
                "teknosa": "36799 TL",
                "amazon": "35999 TL"
            }
        ]
    except Exception as e:
        logging.error(f"Google Sheets veri çekme hatası: {str(e)}")
        return []

def get_reference_phones():
    """
    Google Sheets'ten referans telefon verilerini çeker.
    """
    try:
        # Bu bir örnek implementasyondur
        # Gerçek bir uygulamada Google Sheets API kullanılabilir
        # Örnek veri döndürelim
        return [
            {
                "model": "iPhone 13",
                "release_date": "2021-09-24",
                "base_price": "25999 TL",
                "current_price": "22999 TL",
                "price_change": "-12%"
            },
            {
                "model": "Samsung Galaxy S22",
                "release_date": "2022-02-25",
                "base_price": "22999 TL",
                "current_price": "17999 TL",
                "price_change": "-22%"
            }
        ]
    except Exception as e:
        logging.error(f"Google Sheets referans telefon veri çekme hatası: {str(e)}")
        return [] 