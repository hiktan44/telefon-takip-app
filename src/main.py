#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import sys
import re

# Projenin ana dizinini sys.path'e ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
print(f"Proje kök dizini: {project_root}")
print(f"Mevcut dizin: {current_dir}")

# sys.path'e proje dizinini ekle
sys.path.insert(0, project_root)
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(project_root, 'src'))

# Modül yollarını göster
print(f"Python modül yolları: {sys.path}")

# Yerel modüller
from utils.database import PhoneDatabase
from utils.export import export_to_excel, export_to_html
from scrapers.mediamarkt_scraper import MediaMarktScraper
from scrapers.teknosa_scraper import TeknosaWebScraper
from scrapers.vatan_scraper import VatanWebScraper
from utils.supabase_db import SupabaseDB
from config import SUPABASE_URL, SUPABASE_KEY, PORT, HOST, DEBUG, WEB_HOST, WEB_PORT

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("telefon_takip.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask uygulaması
app = Flask(__name__, 
    static_folder='../static',
    template_folder='../templates'
)

# Veritabanı
db = PhoneDatabase(db_path="telefon_data.db")

# Veri çekici (scraper)
media_markt_scraper = MediaMarktScraper()

# Planlayıcı (scheduler)
scheduler = BackgroundScheduler()

def update_phone_data():
    """Planlı olarak çalışacak fonksiyon - telefon verilerini günceller"""
    try:
        logger.info("Telefon verilerini güncelleme görevi başlatıldı")
        
        # MediaMarkt'tan veri çek
        phones = media_markt_scraper.scrape_all_phones()
        
        # Her telefon için veritabanını güncelle
        for phone in phones:
            model = phone.get("model", "")
            brand = model.split(" ")[0] if " " in model else ""
            price = float(phone.get("price", "0").replace(" TL", "").replace(".", "").replace(",", "."))
            specs = phone.get("specs", {})
            
            db.add_phone(model, brand, price, specs, "MediaMarkt")
        
        logger.info(f"Toplam {len(phones)} telefon verisi güncellendi")
    except Exception as e:
        logger.error(f"Telefon güncelleme görevi hatası: {str(e)}")

# API Route'ları
@app.route('/')
def index():
    """Ana sayfa"""
    phones = db.get_phones(limit=10)
    reference_phones = db.get_reference_phones()
    return render_template('index.html', phones=phones, reference_phones=reference_phones)

@app.route('/phone/<model>')
def phone_detail(model):
    """Telefon detay sayfası"""
    # Arama sonuçlarından benzer modeli bul
    phones = db.get_phones(limit=50)
    phone = None
    
    for p in phones:
        if model.lower() in p["model"].lower():
            phone = p
            break
    
    if not phone:
        return render_template('404.html', message=f"{model} modeli bulunamadı"), 404
    
    # Fiyat geçmişi
    price_history = db.get_price_history(model)
    
    return render_template('phone_detail.html', phone=phone, price_history=price_history)

@app.route('/reference')
def reference_form():
    """Referans telefon giriş formu"""
    return render_template('reference_form.html')

@app.route('/api/reference', methods=['POST'])
def add_reference():
    """Referans telefon ekleme API'si"""
    try:
        data = request.form
        
        model = data.get('model')
        brand = data.get('brand')
        release_date = data.get('release_date')
        base_price = float(data.get('base_price', 0).replace(',', '.'))
        
        # Teknik Özellikler
        specs = {
            "screen": data.get('screen'),
            "processor": data.get('processor'),
            "ram": data.get('ram'),
            "storage": data.get('storage'),
            "battery": data.get('battery'),
            "camera": data.get('camera')
        }
        
        # Veritabanına ekle
        reference_id = db.add_reference_phone(model, brand, release_date, base_price, specs)
        
        if reference_id:
            return jsonify({"success": True, "message": f"Referans telefon eklendi: {brand} {model}", "id": reference_id})
        else:
            return jsonify({"success": False, "message": "Referans telefon eklenirken hata oluştu"}), 500
    except Exception as e:
        logger.error(f"Referans telefon ekleme hatası: {str(e)}")
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500

@app.route('/api/phones')
def get_phones():
    """Telefon listesi API'si"""
    phones = db.get_phones(limit=50)
    return jsonify(phones)

@app.route('/api/reference_phones')
def get_reference_phones():
    """Referans telefon listesi API'si"""
    reference_phones = db.get_reference_phones()
    return jsonify(reference_phones)

@app.route('/api/price_history/<model>')
def get_price_history(model):
    """Fiyat geçmişi API'si"""
    price_history = db.get_price_history(model)
    return jsonify(price_history)

@app.route('/api/export/excel')
def export_excel():
    """Excel export API'si"""
    try:
        # Telefon verilerini al
        phones = db.get_phones(limit=50)
        
        # Excel'e aktar
        file_path = export_to_excel(phones)
        
        if file_path and os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"success": False, "message": "Excel dosyası oluşturulamadı"}), 500
    except Exception as e:
        logger.error(f"Excel export hatası: {str(e)}")
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500

@app.route('/api/export/html')
def export_html():
    """HTML export API'si"""
    try:
        # Telefon verilerini al
        phones = db.get_phones(limit=50)
        
        # HTML'e aktar
        file_path = export_to_html(phones)
        
        if file_path and os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"success": False, "message": "HTML raporu oluşturulamadı"}), 500
    except Exception as e:
        logger.error(f"HTML export hatası: {str(e)}")
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500

@app.route('/api/update', methods=['POST'])
def update_data():
    """Verileri güncellemek için API"""
    try:
        update_phone_data()
        return jsonify({"success": True, "message": "Telefonlar başarıyla güncellendi"})
    except Exception as e:
        logger.error(f"Veri güncelleme hatası: {str(e)}")
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500

@app.route('/api/compare', methods=['POST'])
def compare_phones():
    """Telefon karşılaştırma API'si"""
    try:
        data = request.json
        phone_ids = data.get('phone_ids', [])
        
        if not phone_ids or len(phone_ids) < 2:
            return jsonify({"success": False, "message": "En az 2 telefon seçmelisiniz"}), 400
        
        # Telefon verilerini al
        phones = []
        for phone_id in phone_ids:
            # Burada gerçek bir uygulamada veritabanından ID ile telefon çekilir
            # Örnek olarak:
            # phone = db.get_phone_by_id(phone_id)
            # Şimdilik tüm telefonları çekip ID ile filtreleme yapalım
            all_phones = db.get_phones(limit=100)
            for p in all_phones:
                if p["id"] == phone_id:
                    phones.append(p)
                    break
        
        if len(phones) < 2:
            return jsonify({"success": False, "message": "Yeterli telefon bulunamadı"}), 404
        
        # Karşılaştırma mantığı
        comparison = {
            "phones": phones,
            "differences": [],
            "similarities": []
        }
        
        # Basit bir karşılaştırma örneği
        reference = phones[0]  # İlk telefonu referans olarak al
        specs_to_compare = ["screen", "processor", "ram", "storage"]
        
        for phone in phones[1:]:
            for spec in specs_to_compare:
                if reference["specs"].get(spec) == phone["specs"].get(spec):
                    comparison["similarities"].append({
                        "spec": spec,
                        "value": reference["specs"].get(spec)
                    })
                else:
                    comparison["differences"].append({
                        "spec": spec,
                        "reference_value": reference["specs"].get(spec),
                        "compared_value": phone["specs"].get(spec)
                    })
        
        return jsonify({"success": True, "comparison": comparison})
    except Exception as e:
        logger.error(f"Karşılaştırma hatası: {str(e)}")
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500

@app.errorhandler(404)
def page_not_found(e):
    """404 sayfa bulunamadı hatası"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """500 sunucu hatası"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Ana klasörleri oluştur
    os.makedirs('exports', exist_ok=True)
    
    # Scheduler'ı başlat
    scheduler.add_job(update_phone_data, 'interval', hours=12)
    scheduler.start()
    
    # Flask uygulamasını başlat
    app.run(debug=True, host='0.0.0.0', port=8080) 