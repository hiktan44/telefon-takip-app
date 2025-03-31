import sqlite3
import logging
import json
import os
from datetime import datetime

class PhoneDatabase:
    """
    Telefon verileri için basit bir SQLite veritabanı arayüzü
    """
    def __init__(self, db_path="phone_data.db"):
        self.db_path = db_path
        self.initialize_db()
        
    def initialize_db(self):
        """Veritabanını ve tabloları oluşturur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Telefonlar tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS phones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                brand TEXT,
                price REAL,
                specs TEXT,
                source TEXT,
                date_added TEXT
            )
            ''')
            
            # Referans telefonlar tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reference_phones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                brand TEXT,
                release_date TEXT,
                base_price REAL,
                specs TEXT,
                date_added TEXT
            )
            ''')
            
            # Fiyat geçmişi tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_id INTEGER,
                price REAL,
                date TEXT,
                source TEXT,
                FOREIGN KEY (phone_id) REFERENCES phones (id)
            )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("Veritabanı başarıyla başlatıldı")
        except Exception as e:
            logging.error(f"Veritabanı başlatma hatası: {str(e)}")
    
    def add_phone(self, model, brand, price, specs, source):
        """Yeni bir telefon ekler"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # JSON formatında kaydetmek için specs dict'i stringe çevir
            specs_json = json.dumps(specs)
            
            cursor.execute('''
            INSERT INTO phones (model, brand, price, specs, source, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (model, brand, price, specs_json, source, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            phone_id = cursor.lastrowid
            
            # Fiyat geçmişine de ekle
            cursor.execute('''
            INSERT INTO price_history (phone_id, price, date, source)
            VALUES (?, ?, ?, ?)
            ''', (phone_id, price, datetime.now().strftime("%Y-%m-%d"), source))
            
            conn.commit()
            conn.close()
            logging.info(f"Telefon eklendi: {brand} {model}")
            return phone_id
        except Exception as e:
            logging.error(f"Telefon ekleme hatası: {str(e)}")
            return None
    
    def add_reference_phone(self, model, brand, release_date, base_price, specs):
        """Referans telefon ekler"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # JSON formatında kaydetmek için specs dict'i stringe çevir
            specs_json = json.dumps(specs)
            
            cursor.execute('''
            INSERT INTO reference_phones (model, brand, release_date, base_price, specs, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (model, brand, release_date, base_price, specs_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            reference_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            logging.info(f"Referans telefon eklendi: {brand} {model}")
            return reference_id
        except Exception as e:
            logging.error(f"Referans telefon ekleme hatası: {str(e)}")
            return None
    
    def get_phones(self, limit=10):
        """Telefonları listeler"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM phones ORDER BY date_added DESC LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            phones = []
            
            for row in rows:
                phone = dict(row)
                # JSON'dan dict'e çevir
                phone['specs'] = json.loads(phone['specs'])
                phones.append(phone)
            
            conn.close()
            return phones
        except Exception as e:
            logging.error(f"Telefonları listeleme hatası: {str(e)}")
            return []
    
    def get_reference_phones(self):
        """Referans telefonları listeler"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM reference_phones ORDER BY date_added DESC
            ''')
            
            rows = cursor.fetchall()
            reference_phones = []
            
            for row in rows:
                phone = dict(row)
                # JSON'dan dict'e çevir
                phone['specs'] = json.loads(phone['specs'])
                reference_phones.append(phone)
            
            conn.close()
            return reference_phones
        except Exception as e:
            logging.error(f"Referans telefonları listeleme hatası: {str(e)}")
            return []
    
    def get_price_history(self, model=None, days=30):
        """Fiyat geçmişini çeker"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if model:
                cursor.execute('''
                SELECT p.model, p.brand, ph.price, ph.date, ph.source
                FROM price_history ph
                JOIN phones p ON ph.phone_id = p.id
                WHERE p.model LIKE ?
                ORDER BY ph.date DESC
                ''', (f'%{model}%',))
            else:
                cursor.execute('''
                SELECT p.model, p.brand, ph.price, ph.date, ph.source
                FROM price_history ph
                JOIN phones p ON ph.phone_id = p.id
                ORDER BY ph.date DESC
                ''')
            
            rows = cursor.fetchall()
            price_history = [dict(row) for row in rows]
            
            conn.close()
            return price_history
        except Exception as e:
            logging.error(f"Fiyat geçmişi çekme hatası: {str(e)}")
            return [] 