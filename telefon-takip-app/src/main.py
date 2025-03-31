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
from flask_socketio import SocketIO, emit
import re

# Projenin ana dizinini sys.path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Yerel modüller
from utils.supabase_db import SupabaseDB
from utils.export import export_to_excel, export_to_html
from scrapers.mediamarkt_scraper import MediaMarktScraper
from scrapers.teknosa_scraper import TeknosaWebScraper
from scrapers.vatan_scraper import VatanWebScraper
from config import SUPABASE_URL, SUPABASE_KEY, PORT, HOST, DEBUG, WEB_HOST, WEB_PORT

# Logging yapılandırması
logging.basicConfig(
    level=logging.DEBUG,  # INFO yerine DEBUG kullanıyoruz
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
socketio = SocketIO(app)

# Veritabanı
db = SupabaseDB(SUPABASE_URL, SUPABASE_KEY)

# Veri çekiciler (scrapers)
media_markt_scraper = MediaMarktScraper()
teknosa_scraper = TeknosaWebScraper()
vatan_scraper = VatanWebScraper()

# Scraper listesi
scrapers = {
    'mediamarkt': media_markt_scraper,
    'teknosa': teknosa_scraper,
    'vatan': vatan_scraper
}

# Planlayıcı (scheduler)
scheduler = BackgroundScheduler()

def update_phone_data():
    """Zamanlanmış olarak telefon verilerini günceller"""
    try:
        logger.info("Telefon verilerini güncelleme işlemi başlatılıyor...")
        
        # Tüm telefon scraper'larını başlat
        media_markt_scraper = MediaMarktScraper()
        teknosa_scraper = TeknosaWebScraper()
        vatan_scraper = VatanWebScraper()
        
        # WebSocket ile istemciye bildir
        socketio.emit('scraping_status', {'status': 'started', 'message': 'Veri çekme işlemi başladı'})
        
        # Her scraper için ayrı bir durum nesnesi oluştur
        scraping_status = {
            'MediaMarkt': {'status': 'pending', 'progress': 0, 'error': None, 'count': 0},
            'Teknosa': {'status': 'pending', 'progress': 0, 'error': None, 'count': 0},
            'Vatan': {'status': 'pending', 'progress': 0, 'error': None, 'count': 0}
        }
        
        # WebSocket ile istemciye güncel scraping durumunu gönder
        socketio.emit('scraping_progress', scraping_status)
        
        # MediaMarkt veri çekme
        logger.info("MediaMarkt verilerini çekme işlemi başlatılıyor...")
        scraping_status['MediaMarkt']['status'] = 'in_progress'
        socketio.emit('scraping_progress', scraping_status)
        
        def media_markt_progress_callback(current, total, error=None, message=None):
            scraping_status['MediaMarkt']['progress'] = int((current / total) * 100)
            if error:
                scraping_status['MediaMarkt']['error'] = error
            socketio.emit('scraping_progress', scraping_status)
        
        media_markt_phones = media_markt_scraper.scrape_all_phones(progress_callback=media_markt_progress_callback)
        scraping_status['MediaMarkt']['status'] = 'completed'
        scraping_status['MediaMarkt']['count'] = len(media_markt_phones)
        if len(media_markt_phones) == 0:
            scraping_status['MediaMarkt']['error'] = 'MediaMarkt\'tan telefon verisi çekilemedi.'
        socketio.emit('scraping_progress', scraping_status)
        logger.info(f"MediaMarkt verilerini çekme tamamlandı. {len(media_markt_phones)} adet telefon bulundu.")
        
        # Teknosa veri çekme
        logger.info("Teknosa verilerini çekme işlemi başlatılıyor...")
        scraping_status['Teknosa']['status'] = 'in_progress'
        socketio.emit('scraping_progress', scraping_status)
        
        def teknosa_progress_callback(current, total, error=None, message=None):
            scraping_status['Teknosa']['progress'] = int((current / total) * 100)
            if error:
                scraping_status['Teknosa']['error'] = error
            socketio.emit('scraping_progress', scraping_status)
        
        teknosa_phones = teknosa_scraper.scrape_all_phones(progress_callback=teknosa_progress_callback)
        scraping_status['Teknosa']['status'] = 'completed'
        scraping_status['Teknosa']['count'] = len(teknosa_phones)
        if len(teknosa_phones) == 0:
            scraping_status['Teknosa']['error'] = 'Teknosa\'dan telefon verisi çekilemedi.'
        socketio.emit('scraping_progress', scraping_status)
        logger.info(f"Teknosa verilerini çekme tamamlandı. {len(teknosa_phones)} adet telefon bulundu.")
        
        # Vatan veri çekme
        logger.info("Vatan Bilgisayar verilerini çekme işlemi başlatılıyor...")
        scraping_status['Vatan']['status'] = 'in_progress'
        socketio.emit('scraping_progress', scraping_status)
        
        def vatan_progress_callback(current, total, error=None, message=None):
            scraping_status['Vatan']['progress'] = int((current / total) * 100)
            if error:
                scraping_status['Vatan']['error'] = error
            socketio.emit('scraping_progress', scraping_status)
        
        vatan_phones = vatan_scraper.scrape_all_phones(progress_callback=vatan_progress_callback)
        scraping_status['Vatan']['status'] = 'completed'
        scraping_status['Vatan']['count'] = len(vatan_phones)
        if len(vatan_phones) == 0:
            scraping_status['Vatan']['error'] = 'Vatan Bilgisayar\'dan telefon verisi çekilemedi.'
        socketio.emit('scraping_progress', scraping_status)
        logger.info(f"Vatan Bilgisayar verilerini çekme tamamlandı. {len(vatan_phones)} adet telefon bulundu.")
        
        # Telefonları birleştir
        all_phones = media_markt_phones + teknosa_phones + vatan_phones
        
        # Telefonları veritabanına kaydet
        save_phones_to_database(all_phones)
        
        # İşlem tamamlandı
        total_count = len(all_phones)
        if total_count == 0:
            finish_message = "Veri çekme işlemi tamamlandı, ancak hiçbir siteden telefon verisi çekilemedi."
            logger.warning(finish_message)
        else:
            finish_message = f"Veri çekme işlemi tamamlandı. Toplam {total_count} adet telefon çekildi."
            logger.info(finish_message)
        
        socketio.emit('scraping_status', {
            'status': 'completed', 
            'message': finish_message,
            'total_count': total_count
        })
        
        return True
    except Exception as e:
        error_message = f"Veri çekme işlemi sırasında hata oluştu: {str(e)}"
        logger.error(error_message)
        socketio.emit('scraping_status', {'status': 'error', 'message': error_message})
        return False

# Zamanlanmış görevleri ekle
scheduler.add_job(update_phone_data, 'interval', hours=1, id='update_phone_data')

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
        logger.debug("Referans telefon ekleme isteği alındı")
        data = request.get_json()
        logger.debug(f"Alınan veri: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if not data:
            logger.error("Gelen veri boş")
            return jsonify({
                "success": False,
                "message": "Geçersiz veri formatı"
            }), 400
        
        if not data.get('model') or not data.get('brand'):
            logger.error("Model veya marka alanı eksik")
            return jsonify({
                "success": False, 
                "message": "Model ve marka alanları zorunludur"
            }), 400
        
        model = data.get('model')
        brand = data.get('brand')
        release_date = data.get('release_date')
        
        # Fiyatı düzgün bir şekilde işle
        try:
            base_price = float(str(data.get('base_price', '0')).replace('.', '').replace(',', '.'))
            logger.debug(f"İşlenen fiyat: {base_price}")
        except (ValueError, TypeError) as e:
            logger.error(f"Fiyat dönüştürme hatası: {str(e)}")
            base_price = 0
        
        # Teknik özellikleri al
        specs = data.get('specs', {})
        logger.debug(f"İşlenecek özellikler: {json.dumps(specs, indent=2, ensure_ascii=False)}")
        
        # Veritabanına ekle
        try:
            reference_id = db.add_reference_phone(model, brand, release_date, base_price, specs)
            logger.debug(f"Veritabanı işlem sonucu - reference_id: {reference_id}")
            
            if reference_id:
                logger.info(f"Referans telefon başarıyla eklendi. ID: {reference_id}")
                return jsonify({
                    "success": True, 
                    "message": f"Referans telefon eklendi: {brand} {model}", 
                    "id": reference_id
                })
            else:
                logger.error("Veritabanına ekleme başarısız oldu - ID alınamadı")
                return jsonify({
                    "success": False, 
                    "message": "Referans telefon eklenemedi. Lütfen tekrar deneyin."
                }), 500
                
        except Exception as db_error:
            error_message = str(db_error)
            if "row-level security" in error_message.lower():
                logger.error(f"Supabase güvenlik politikası hatası: {error_message}")
                return jsonify({
                    "success": False,
                    "message": "Güvenlik politikası nedeniyle sunucu veritabanına eklenemedi, ancak veriler yerel olarak kaydedildi. Referans telefonu görüntüleyebilirsiniz."
                }), 200
            else:
                logger.error(f"Veritabanı işlem hatası: {error_message}")
                return jsonify({
                    "success": False,
                    "message": f"Veritabanı hatası: {error_message}"
                }), 500
            
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}", exc_info=True)
        return jsonify({
            "success": False, 
            "message": f"Beklenmeyen bir hata oluştu: {str(e)}"
        }), 500

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

@app.route('/api/phones/processor/<processor>')
def get_phones_by_processor(processor):
    """İşlemciye göre telefon listesi API'si"""
    phones = db.get_phones_by_processor(processor)
    return jsonify(phones)

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

@app.route('/update_data')
def update_data():
    """Verileri manuel olarak güncelle"""
    try:
        logger.info("Manuel veri güncelleme isteği alındı")
        # Arka planda çalıştırmak yerine doğrudan çalıştır
        update_phone_data()
        return jsonify({
            'status': 'success', 
            'message': 'Veri güncelleme işlemi başlatıldı. İşlem tamamlandığında bildirim alacaksınız.'
        })
    except Exception as e:
        logger.error(f"Veri güncelleme hatası: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Veri güncelleme hatası: {str(e)}'
        }), 500

# Belirli bir kaynaktan veri güncelleme
@app.route('/update_data/<source>')
def update_source_data(source):
    """Belirli bir kaynaktan verileri güncelle"""
    try:
        logger.info(f"{source} için veri güncelleme isteği alındı")
        
        if source not in scrapers:
            return jsonify({
                'status': 'error',
                'message': f'Geçersiz kaynak: {source}'
            }), 400
            
        # İlerleme durumunu sıfırla
        socketio.emit('scraping_progress', {
            'source': source,
            'progress': 0,
            'status': 'başladı'
        })
        
        # Veri çek
        scraper = scrapers[source]
        phones = scraper.scrape_all_phones(
            progress_callback=lambda current, total, error=None, message=None: socketio.emit('scraping_progress', {
                'source': source,
                'progress': int(current),
                'status': 'devam ediyor' if not error else 'hata',
                'error': error,
                'message': message
            })
        )
        
        # Veritabanına ekle
        success_count = 0
        for phone in phones:
            try:
                model = phone.get("model", "")
                brand = model.split(" ")[0] if " " in model else ""
                price_str = phone.get("price", "0")
                
                # Fiyat string işleme
                if isinstance(price_str, str):
                    price_str = price_str.replace(" TL", "").replace(".", "").replace(",", ".")
                    price = float(price_str)
                else:
                    price = float(price_str)
                
                specs = phone.get("specs", {})
                
                # Veritabanına ekle
                phone_id = db.add_phone(model, brand, price, specs, source.capitalize())
                
                if phone_id:
                    success_count += 1
                    logger.debug(f"Telefon eklendi: {brand} {model}")
            except Exception as e:
                logger.error(f"Telefon ekleme hatası: {str(e)}")
                continue
                
        # İşlem tamamlandı
        logger.info(f"{source} sitesinden toplam {len(phones)} telefondan {success_count} tanesi başarıyla eklendi")
        socketio.emit('scraping_progress', {
            'source': source,
            'progress': 100,
            'status': 'tamamlandı',
            'message': f"{success_count} telefon verisi güncellendi"
        })
            
        return jsonify({
            'status': 'success',
            'message': f'{source} için veri güncelleme tamamlandı.'
        })
        
    except Exception as e:
        logger.error(f"{source} veri güncelleme hatası: {str(e)}", exc_info=True)
        socketio.emit('scraping_progress', {
            'source': source,
            'progress': 0,
            'status': 'hata',
            'error': str(e)
        })
        return jsonify({
            'status': 'error',
            'message': f'Veri güncelleme hatası: {str(e)}'
        }), 500

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

@app.route('/api/phones/search', methods=['POST'])
def search_phones():
    """Telefonları ara ve filtreleme uygula"""
    try:
        request_data = request.get_json(silent=True) or {}
        
        # Filtre parametreleri
        min_price = float(request_data.get('min_price', 0))
        max_price = float(request_data.get('max_price', 100000))
        brands = request_data.get('brands', [])
        sources = request_data.get('sources', [])
        sort_by = request_data.get('sort_by', 'price')
        sort_order = request_data.get('sort_order', 'asc')
        ram_filter = request_data.get('ram', '')
        storage_filter = request_data.get('storage', '')
        keyword = request_data.get('keyword', '').lower()
        
        # Telefonları veri tabanından al
        phones_data = get_phones_from_database()
        
        if not phones_data:
            socketio.emit('search_complete', {
                'success': False,
                'error': 'Telefon verisi bulunamadı. Hiçbir siteden veri çekilemedi veya veritabanında veri yok.',
                'total': 0
            })
            return jsonify({
                'success': False,
                'error': 'Telefon verisi bulunamadı. Hiçbir siteden veri çekilemedi veya veritabanında veri yok.',
                'phones': [],
                'total': 0
            })
        
        # Telefonları filtrele
        filtered_phones = []
        
        for phone in phones_data:
            try:
                # Fiyat bilgisi
                price = get_phone_price(phone)
                if not min_price <= price <= max_price:
                    continue
                
                # Marka filtresi
                if brands and phone['model'].split(' ')[0].lower() not in [b.lower() for b in brands]:
                    continue
                
                # Kaynak filtresi
                if sources and phone['source'].lower() not in [s.lower() for s in sources]:
                    continue
                
                # RAM filtresi
                if ram_filter and not _matches_ram_filter(phone.get('specs', {}).get('ram_rom', ''), ram_filter):
                    continue
                
                # Depolama filtresi  
                if storage_filter and not _matches_storage_filter(phone.get('specs', {}).get('ram_rom', ''), storage_filter):
                    continue
                
                # Anahtar kelime filtresi
                if keyword and keyword not in phone['model'].lower():
                    continue
                
                filtered_phones.append(phone)
            except Exception as e:
                print(f"Telefon filtreleme hatası: {str(e)}")
                continue
        
        # Verileri sırala
        sorted_phones = sort_phones(filtered_phones, sort_by, sort_order)
        
        # WebSocket ile istemciye bildir
        socketio.emit('search_complete', {
            'success': True,
            'total': len(sorted_phones)
        })
        
        return jsonify({
            'success': True,
            'phones': sorted_phones,
            'total': len(sorted_phones)
        })
    except Exception as e:
        print(f"Arama hatası: {str(e)}")
        socketio.emit('search_complete', {
            'success': False,
            'error': str(e),
            'total': 0
        })
        return jsonify({
            'success': False,
            'error': str(e),
            'phones': [],
            'total': 0
        })

@app.errorhandler(404)
def page_not_found(e):
    """404 sayfa bulunamadı hatası"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """500 sunucu hatası"""
    return render_template('500.html'), 500

# WebSocket işleyiciler
@socketio.on('connect')
def handle_connect():
    """WebSocket bağlantısı kurulduğunda"""
    logger.info("WebSocket bağlantısı kuruldu")
    
@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket bağlantısı kapatıldığında"""
    logger.info("WebSocket bağlantısı kapatıldı")
    
@socketio.on('request_update')
def handle_request_update():
    """İstemciden veri güncelleme isteği geldiğinde"""
    logger.info("İstemciden veri güncelleme isteği alındı")
    # Arka planda güncelleme işlemini başlat
    update_phone_data()

@socketio.on('request_source_update')
def handle_source_update(data):
    """İstemciden belirli bir kaynağı güncelleme isteği geldiğinde"""
    source = data.get('source')
    if source and source in scrapers:
        logger.info(f"İstemciden {source} için güncelleme isteği alındı")
        
        # İşlemi gerçekleştir
        try:
            # İlerleme durumunu sıfırla
            socketio.emit('scraping_progress', {
                'source': source,
                'progress': 0,
                'status': 'başladı'
            })
            
            # Veri çek
            scraper = scrapers[source]
            phones = scraper.scrape_all_phones(
                progress_callback=lambda current, total, error=None, message=None: socketio.emit('scraping_progress', {
                    'source': source,
                    'progress': int(current),
                    'status': 'devam ediyor' if not error else 'hata',
                    'error': error,
                    'message': message
                })
            )
            
            # Veritabanına ekle
            success_count = 0
            for phone in phones:
                try:
                    model = phone.get("model", "")
                    brand = model.split(" ")[0] if " " in model else ""
                    price_str = phone.get("price", "0")
                    
                    # Fiyat string işleme
                    if isinstance(price_str, str):
                        price_str = price_str.replace(" TL", "").replace(".", "").replace(",", ".")
                        price = float(price_str)
                    else:
                        price = float(price_str)
                    
                    specs = phone.get("specs", {})
                    
                    # Veritabanına ekle
                    phone_id = db.add_phone(model, brand, price, specs, source.capitalize())
                    
                    if phone_id:
                        success_count += 1
                        logger.debug(f"Telefon eklendi: {brand} {model}")
                except Exception as e:
                    logger.error(f"Telefon ekleme hatası: {str(e)}")
                    continue
                    
            # İşlem tamamlandı
            logger.info(f"{source} sitesinden toplam {len(phones)} telefondan {success_count} tanesi başarıyla eklendi")
            socketio.emit('scraping_progress', {
                'source': source,
                'progress': 100,
                'status': 'tamamlandı',
                'message': f"{success_count} telefon verisi güncellendi"
            })
                
        except Exception as e:
            logger.error(f"{source} veri güncelleme hatası: {str(e)}", exc_info=True)
            socketio.emit('scraping_progress', {
                'source': source,
                'progress': 0,
                'status': 'hata',
                'error': str(e)
            })

def save_phones_to_database(phones):
    """
    Telefonları veritabanına kaydeder
    
    Args:
        phones (list): Kaydedilecek telefonlar listesi
    
    Returns:
        int: Başarıyla kaydedilen telefon sayısı
    """
    try:
        if not phones:
            logger.warning("Kaydedilecek telefon yok")
            return 0
            
        # Supabase bağlantısını al
        supabase_client = get_supabase_client()
        
        # Mevcut telefonları temizle (her seferinde tümünü güncelliyoruz)
        # supabase_client.table("phones").delete().execute()
        
        # Her telefonu veritabanına ekle
        success_count = 0
        for phone in phones:
            try:
                # Telefon verisini Supabase formatına dönüştür
                phone_data = {
                    "model": phone.get("model", ""),
                    "brand": phone.get("model", "").split(" ")[0] if " " in phone.get("model", "") else "",
                    "price": _normalize_price(phone.get("price", "0")),
                    "specs": phone.get("specs", {}),
                    "source": phone.get("source", ""),
                    "source_url": phone.get("source_url", ""),
                    "updated_at": datetime.now().isoformat()
                }
                
                # Supabase'e ekle
                result = supabase_client.table("phones").insert(phone_data).execute()
                
                if result and len(result.data) > 0:
                    success_count += 1
                    logger.debug(f"Telefon eklendi: {phone_data['brand']} {phone_data['model']}")
                
            except Exception as e:
                logger.error(f"Telefon kaydetme hatası: {str(e)}")
                continue
                
        logger.info(f"Veritabanına toplam {success_count}/{len(phones)} telefon kaydedildi")
        return success_count
        
    except Exception as e:
        logger.error(f"Veritabanına kaydetme hatası: {str(e)}")
        return 0

def get_phones_from_database():
    """
    Veritabanından telefonları alır
    
    Returns:
        list: Telefonlar listesi
    """
    try:
        # Supabase bağlantısını al
        supabase_client = get_supabase_client()
        
        # Telefonları çek
        result = supabase_client.table("phones").select("*").execute()
        
        if result and hasattr(result, 'data'):
            logger.info(f"Veritabanından {len(result.data)} telefon alındı")
            return result.data
            
        logger.warning("Veritabanından telefon alınamadı")
        return []
        
    except Exception as e:
        logger.error(f"Veritabanından veri alma hatası: {str(e)}")
        return []

def _normalize_price(price):
    """
    Fiyat string işleme
    
    Args:
        price: Fiyat string veya sayı
        
    Returns:
        float: Normalize edilmiş fiyat
    """
    if isinstance(price, (int, float)):
        return float(price)
        
    if not price:
        return 0.0
    
    price_str = str(price).strip()
    price_str = price_str.replace(" TL", "").replace("TL", "").replace("₺", "").strip()
    price_str = price_str.replace(".", "").replace(",", ".").strip()
    
    try:
        return float(price_str)
    except ValueError:
        logger.error(f"Fiyat dönüştürme hatası: {price_str}")
        return 0.0

def get_phone_price(phone):
    """
    Telefon fiyatını alır
    
    Args:
        phone (dict): Telefon verisi
        
    Returns:
        float: Fiyat
    """
    price = phone.get("price", 0)
    return _normalize_price(price)

def _matches_ram_filter(ram_rom_str, ram_filter):
    """
    RAM filtrelerine uygunluğu kontrol eder
    
    Args:
        ram_rom_str (str): RAM+ROM string (örn: "8GB + 128GB")
        ram_filter (str): RAM filtresi (örn: "8GB")
        
    Returns:
        bool: Eşleşme durumu
    """
    if not ram_filter or not ram_rom_str:
        return True
        
    try:
        # RAM değerini al (örn: "8GB + 128GB" -> "8GB")
        ram_part = ram_rom_str.split("+")[0].strip() if "+" in ram_rom_str else ram_rom_str
        
        # Sayı kısmını çıkar
        ram_value = int(re.search(r'\d+', ram_part).group(0)) if re.search(r'\d+', ram_part) else 0
        filter_value = int(re.search(r'\d+', ram_filter).group(0)) if re.search(r'\d+', ram_filter) else 0
        
        return ram_value >= filter_value
    except Exception as e:
        logger.error(f"RAM filtre eşleştirme hatası: {str(e)}")
        return True

def _matches_storage_filter(ram_rom_str, storage_filter):
    """
    Depolama filtrelerine uygunluğu kontrol eder
    
    Args:
        ram_rom_str (str): RAM+ROM string (örn: "8GB + 128GB")
        storage_filter (str): Depolama filtresi (örn: "128GB")
        
    Returns:
        bool: Eşleşme durumu
    """
    if not storage_filter or not ram_rom_str:
        return True
        
    try:
        # Depolama değerini al (örn: "8GB + 128GB" -> "128GB")
        storage_part = ram_rom_str.split("+")[1].strip() if "+" in ram_rom_str else ram_rom_str
        
        # Sayı kısmını çıkar
        storage_value = int(re.search(r'\d+', storage_part).group(0)) if re.search(r'\d+', storage_part) else 0
        filter_value = int(re.search(r'\d+', storage_filter).group(0)) if re.search(r'\d+', storage_filter) else 0
        
        return storage_value >= filter_value
    except Exception as e:
        logger.error(f"Depolama filtre eşleştirme hatası: {str(e)}")
        return True

def sort_phones(phones, sort_by='price', sort_order='asc'):
    """
    Telefonları sıralar
    
    Args:
        phones (list): Telefonlar listesi
        sort_by (str): Sıralama alanı (price, model, brand)
        sort_order (str): Sıralama yönü (asc, desc)
        
    Returns:
        list: Sıralanmış telefonlar listesi
    """
    try:
        if not phones:
            return []
            
        sorted_phones = phones.copy()
        
        # Sıralama fonksiyonu
        if sort_by == 'price':
            sorted_phones.sort(key=lambda x: get_phone_price(x), reverse=(sort_order == 'desc'))
        elif sort_by == 'model':
            sorted_phones.sort(key=lambda x: x.get('model', ''), reverse=(sort_order == 'desc'))
        elif sort_by == 'brand':
            sorted_phones.sort(key=lambda x: x.get('model', '').split(' ')[0] if ' ' in x.get('model', '') else '', reverse=(sort_order == 'desc'))
        
        return sorted_phones
    except Exception as e:
        logger.error(f"Telefon sıralama hatası: {str(e)}")
        return phones

if __name__ == '__main__':
    print("Uygulama başlatılıyor...")
    print(f"Host: {WEB_HOST}")
    print(f"Port: {WEB_PORT}")
    print(f"Debug: {DEBUG}")
    socketio.run(app, host=WEB_HOST, port=WEB_PORT, debug=DEBUG, allow_unsafe_werkzeug=True) 