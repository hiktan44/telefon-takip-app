from supabase import create_client
import os
import json
import logging
from datetime import datetime
import requests

class SupabaseDB:
    """Supabase veritabanı işlemleri için wrapper sınıf"""
    
    def __init__(self, url, key):
        """
        Supabase bağlantısını oluşturur
        
        Args:
            url (str): Supabase URL'si
            key (str): Supabase API anahtarı
        """
        try:
            # Supabase bağlantısını kurma
            self.supabase = create_client(url, key)
            logging.info("Supabase bağlantısı başarılı")
        except Exception as e:
            logging.error(f"Supabase bağlantı hatası: {str(e)}")
            raise e
    
    def get_phones(self):
        """Tüm telefonları veritabanından alır"""
        try:
            # Telefonları çek
            response = self.supabase.table("phones").select("*").execute()
            
            # Yanıtı kontrol et
            if response and hasattr(response, 'data') and len(response.data) > 0:
                phones = response.data
                logging.info(f"Veritabanından {len(phones)} telefon alındı")
                return phones
            else:
                logging.warning("Veritabanında telefon bulunamadı")
                return []
                
        except Exception as e:
            logging.error(f"Telefonları getirme hatası: {str(e)}")
            return []
    
    def add_phone(self, model, brand, price, specs, source, source_url=None):
        """
        Telefon bilgisini veritabanına ekler
        
        Args:
            model (str): Telefon modeli
            brand (str): Telefon markası
            price (float): Fiyat
            specs (dict): Özellikler
            source (str): Veri kaynağı
            source_url (str, optional): Kaynak URL
            
        Returns:
            dict: Eklenen telefon bilgisi
        """
        try:
            # Telefon verisini hazırla
            phone_data = {
                "model": model,
                "brand": brand,
                "price": price,
                "specs": json.dumps(specs),  # JSON'a dönüştür
                "source": source,
                "source_url": source_url
            }
            
            # Veritabanına ekle
            response = self.supabase.table("phones").insert(phone_data).execute()
            
            # Yanıtı kontrol et
            if response and hasattr(response, 'data') and len(response.data) > 0:
                logging.info(f"Telefon eklendi: {model}")
                return response.data[0]
            else:
                logging.warning(f"Telefon eklenemedi: {model}")
                return None
                
        except Exception as e:
            logging.error(f"Telefon ekleme hatası: {str(e)}")
            return None
    
    def search_phones(self, keyword=None, min_price=None, max_price=None, brands=None, sources=None):
        """
        Telefonları filtreler
        
        Args:
            keyword (str, optional): Arama anahtar kelimesi
            min_price (float, optional): Minimum fiyat
            max_price (float, optional): Maximum fiyat
            brands (list, optional): Marka listesi
            sources (list, optional): Kaynak listesi
            
        Returns:
            list: Filtrelenmiş telefonlar
        """
        try:
            # Supabase sorgusu oluştur
            query = self.supabase.table("phones").select("*")
            
            # Filtreleri uygula
            if keyword:
                query = query.ilike("model", f"%{keyword}%")
                
            if min_price is not None:
                query = query.gte("price", min_price)
                
            if max_price is not None:
                query = query.lte("price", max_price)
                
            if brands and len(brands) > 0:
                query = query.in_("brand", brands)
                
            if sources and len(sources) > 0:
                query = query.in_("source", sources)
            
            # Sorguyu çalıştır
            response = query.execute()
            
            # Yanıtı kontrol et
            if response and hasattr(response, 'data') and len(response.data) > 0:
                phones = response.data
                logging.info(f"Filtreli sorguda {len(phones)} telefon bulundu")
                return phones
            else:
                logging.warning("Filtreli sorguda telefon bulunamadı")
                return []
                
        except Exception as e:
            logging.error(f"Telefon arama hatası: {str(e)}")
            return []
    
    def initialize_db(self):
        """
        Supabase'de tabloları oluşturur (sadece ilk kez)
        Not: Supabase Studio'dan manuel olarak da oluşturulabilir
        """
        try:
            # phones tablosu
            self.supabase.table('phones').select('id').limit(1).execute()
            
            # reference_phones tablosu
            self.supabase.table('reference_phones').select('id').limit(1).execute()
            
            # price_history tablosu
            self.supabase.table('price_history').select('id').limit(1).execute()
            
            logging.info("Supabase bağlantısı başarılı")
        except Exception as e:
            logging.error(f"Supabase bağlantı hatası: {str(e)}")
            raise e
    
    def add_reference_phone(self, model, brand, release_date, base_price, specs):
        """Referans telefon ekler"""
        try:
            logging.debug(f"Referans telefon ekleme işlemi başlatıldı: {brand} {model}")
            
            # Veri doğrulama
            if not model or not brand:
                raise ValueError("Model ve marka alanları zorunludur")
            
            # Verileri hazırla
            data = {
                'model': model,
                'brand': brand,
                'release_date': release_date if release_date else None,
                'base_price': float(base_price) if base_price else 0,
                'specs': json.dumps(specs, ensure_ascii=False) if specs else '{}',
                'date_added': datetime.now().isoformat()
            }
            
            logging.debug(f"Hazırlanan veri: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # SQLite'a kaydet (Supabase'deki RLS sorunu nedeniyle)
            try:
                import sqlite3
                import os
                
                db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "telefon_data.db")
                logging.debug(f"SQLite DB yolu: {db_path}")
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Tablo yoksa oluştur
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS reference_phones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    release_date TEXT,
                    base_price REAL,
                    specs TEXT,
                    date_added TEXT
                )
                ''')
                
                cursor.execute('''
                INSERT INTO reference_phones (model, brand, release_date, base_price, specs, date_added)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (model, brand, release_date, base_price, json.dumps(specs, ensure_ascii=False), datetime.now().isoformat()))
                
                conn.commit()
                reference_id = cursor.lastrowid
                conn.close()
                
                logging.info(f"Referans telefon SQLite'a kaydedildi: {brand} {model} (ID: {reference_id})")
                return reference_id
                
            except Exception as sqlite_error:
                logging.error(f"SQLite kaydetme hatası: {str(sqlite_error)}")
                
                # SQLite başarısız olursa, hata bilgisini döndür
                raise Exception(f"Veritabanı işlem hatası (SQLite): {str(sqlite_error)}")
            
        except ValueError as ve:
            logging.error(f"Veri doğrulama hatası: {str(ve)}")
            raise ve
        except Exception as e:
            logging.error(f"Referans telefon ekleme hatası: {str(e)}")
            raise e
    
    def get_reference_phones(self):
        """Referans telefonları listeler"""
        try:
            # Önce Supabase'den çekmeyi dene
            try:
                result = self.supabase.table('reference_phones')\
                    .select('*')\
                    .order('date_added', desc=True)\
                    .execute()
                    
                reference_phones = []
                for phone in result.data:
                    phone['specs'] = json.loads(phone['specs'])
                    reference_phones.append(phone)
                
                if reference_phones:
                    logging.info(f"Supabase'den {len(reference_phones)} referans telefon getirildi")
                    return reference_phones
            except Exception as supabase_error:
                logging.error(f"Supabase'den referans telefonları getirme hatası: {str(supabase_error)}")
            
            # Supabase başarısız olursa SQLite'dan çek
            try:
                import sqlite3
                import os
                
                db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "telefon_data.db")
                
                if not os.path.exists(db_path):
                    logging.warning(f"SQLite veritabanı bulunamadı: {db_path}")
                    return []
                    
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row  # Sözlük benzeri sonuçlar için
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM reference_phones ORDER BY date_added DESC
                ''')
                
                rows = cursor.fetchall()
                conn.close()
                
                reference_phones = []
                for row in rows:
                    row_dict = dict(row)
                    try:
                        row_dict['specs'] = json.loads(row_dict['specs'])
                    except (json.JSONDecodeError, TypeError):
                        row_dict['specs'] = {}
                    reference_phones.append(row_dict)
                    
                logging.info(f"SQLite'dan {len(reference_phones)} referans telefon getirildi")
                return reference_phones
                
            except Exception as sqlite_error:
                logging.error(f"SQLite'dan referans telefonları getirme hatası: {str(sqlite_error)}")
                return []
            
        except Exception as e:
            logging.error(f"Referans telefonları listeleme hatası: {str(e)}")
            return []
    
    def get_phones_by_processor(self, processor):
        """İşlemciye göre telefonları filtreler"""
        try:
            result = self.supabase.table('reference_phones')\
                .select('*')\
                .execute()
                
            phones = []
            for phone in result.data:
                specs = json.loads(phone['specs'])
                if 'processor' in specs and processor.lower() in specs['processor'].lower():
                    phone['specs'] = specs
                    phones.append(phone)
            
            return phones
        except Exception as e:
            logging.error(f"İşlemci filtreleme hatası: {str(e)}")
            return []
    
    def get_price_history(self, model=None, days=30):
        """Fiyat geçmişini çeker"""
        try:
            query = self.supabase.table('price_history')\
                .select('phones(model,brand),price,date,source')\
                .order('date', desc=True)
                
            if model:
                query = query.eq('phones.model', model)
                
            result = query.execute()
            
            price_history = []
            for record in result.data:
                phone_data = record['phones']
                price_history.append({
                    'model': phone_data['model'],
                    'brand': phone_data['brand'],
                    'price': record['price'],
                    'date': record['date'],
                    'source': record['source']
                })
            
            return price_history
        except Exception as e:
            logging.error(f"Fiyat geçmişi çekme hatası: {str(e)}")
            return [] 