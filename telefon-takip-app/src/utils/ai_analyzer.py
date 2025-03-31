import openai
import logging
import json
import os
import sys

# Ana dizini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

# OpenAI API anahtarını ayarla
openai.api_key = OPENAI_API_KEY

def find_similar_phones(reference_phone, all_phones, top_n=5):
    """
    Referans telefona en benzer telefonları yapay zeka kullanarak bulur.
    
    Args:
        reference_phone (dict): Karşılaştırma için referans telefon
        all_phones (list): Tüm telefonların listesi
        top_n (int): Döndürülecek benzer telefon sayısı
        
    Returns:
        list: En benzer telefonların listesi
    """
    try:
        if not OPENAI_API_KEY:
            logger.error("OpenAI API anahtarı tanımlanmamış")
            return []
            
        # Karşılaştırma için JSON verisi oluştur
        comparison_data = {
            "reference_phone": reference_phone,
            "all_phones": all_phones
        }
        
        # Prompt hazırla
        prompt = f"""Aşağıda bir referans telefon ve bir telefon listesi var. Referans telefona en benzer {top_n} telefonu bul. 
        Benzerliği değerlendirirken şu özelliklere göre puanlama yap (önem sırasına göre):
        
        1. İşlemci gücü ve tipi (en önemli)
        2. RAM ve Depolama kapasitesi
        3. Kamera özellikleri ve çözünürlükleri
        4. Ekran kalitesi, teknolojisi ve boyutu
        5. Pil kapasitesi ve şarj hızı
        
        FİYAT ÖZELLİĞİNİ KARŞILAŞTIRMADA DİKKATE ALMA! Fiyat sadece bilgi amaçlı listelenecek.
        
        Özellikle şuna dikkat et: İşlemci gücü, RAM ve kamera özellikleri en önemli karşılaştırma kriterleri olmalı.
        Referans telefonla aynı veya benzer işlemciye sahip telefonlar, benzer RAM ve depolama kapasitesi olanlar üst sıralarda olmalı.
        
        Sonuçları tam olarak Excel tablosunda görüldüğü formatta oluştur.
        
        Referans telefona en çok benzeyen telefonları döndür. Benzerlik skorunu 100 üzerinden hesapla. Sadece benzer telefonları JSON formatında döndür, 
        ekstra açıklama ekleme.
        
        ```
        {json.dumps(comparison_data, ensure_ascii=False, indent=2)}
        ```
        
        JSON çıktı formatı şöyle olmalı:
        ```
        {
          "similar_phones": [
            {
              "name": "Telefon Adı",
              "similarity_score": 95,
              "similar_features": ["İşlemci", "RAM", "Ekran"],
              "different_features": ["Kamera", "Pil"],
              "pros": ["Daha iyi pil ömrü", "Daha fazla depolama"],
              "cons": ["Daha düşük kamera çözünürlüğü"],
              "processor": "İşlemci adı",
              "ram": "RAM değeri",
              "storage": "Depolama değeri",
              "screen": "Ekran özellikleri",
              "battery": "Batarya özellikleri",
              "rear_camera": "Arka kamera değerleri",
              "front_camera": "Ön kamera değerleri"
            }
          ]
        }
        ```
        """
        
        # OpenAI API'ye istek gönder
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Sen bir telefon karşılaştırma uzmanısın. Telefonları teknik özelliklerine göre karşılaştırır ve benzerlik puanları oluşturursun. Fiyat senin için önemli değil, sadece teknik özelliklere odaklanırsın."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        # Sonucu ayrıştır
        content = response.choices[0].message.content
        result = json.loads(content)
        
        return result.get("similar_phones", [])
    except Exception as e:
        logger.error(f"Yapay zeka karşılaştırması sırasında hata: {e}")
        return []

def analyze_phone_reviews(phone_name, reviews):
    """
    Telefon yorumlarını analiz eder ve özetler.
    
    Args:
        phone_name (str): Telefon adı
        reviews (list): Kullanıcı yorumlarının listesi
        
    Returns:
        dict: Yorum analizi sonuçları
    """
    try:
        if not OPENAI_API_KEY or not reviews:
            return {}
            
        # Prompt hazırla
        prompt = f"""Aşağıda {phone_name} için kullanıcı yorumları var. Bu yorumları analiz et ve şunları belirle:
        1. En çok beğenilen özellikler
        2. En çok şikayet edilen özellikler
        3. Genel kullanıcı memnuniyeti (1-5 arası)
        4. Yorumlardan çıkan önemli notlar
        
        Yorumlar:
        ```
        {json.dumps(reviews, ensure_ascii=False)}
        ```
        
        JSON çıktı formatı şöyle olmalı:
        ```
        {
          "liked_features": ["Özellik 1", "Özellik 2", "Özellik 3"],
          "disliked_features": ["Özellik 1", "Özellik 2"],
          "satisfaction_score": 4.2,
          "key_notes": ["Not 1", "Not 2", "Not 3"]
        }
        ```
        
        Sadece JSON formatında yanıt ver, ekstra açıklama yapma.
        """
        
        # OpenAI API'ye istek gönder
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Sen bir ürün yorum analisti uzmanısın. Kullanıcı yorumlarını analiz eder ve özetler çıkarırsın."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Sonucu ayrıştır
        content = response.choices[0].message.content
        result = json.loads(content)
        
        return result
    except Exception as e:
        logger.error(f"Yorum analizi sırasında hata: {e}")
        return {}

def detect_promotions(current_data, previous_data):
    """
    Mevcut ve önceki verileri karşılaştırarak kampanyaları tespit eder.
    
    Args:
        current_data (list): Mevcut telefon verileri
        previous_data (list): Önceki telefon verileri
        
    Returns:
        list: Tespit edilen kampanyaların listesi
    """
    try:
        if not OPENAI_API_KEY or not previous_data:
            return []
            
        # Karşılaştırma verisi oluştur
        comparison_data = {
            "current_data": current_data,
            "previous_data": previous_data
        }
        
        # Prompt hazırla
        prompt = f"""Aşağıda telefonlar için mevcut ve önceki veriler var. Bu verileri karşılaştırarak yeni kampanyaları tespit et.
        Kampanya olarak değerlendirilecek durumlar:
        1. Fiyatta önemli düşüş (en az %10)
        2. Taksit sayısında artış
        3. Peşin kontratlı tekliflerde değişiklik
        
        Veriler:
        ```
        {json.dumps(comparison_data, ensure_ascii=False, indent=2)}
        ```
        
        JSON çıktı formatı şöyle olmalı:
        ```
        {
          "promotions": [
            {
              "phone_name": "Telefon Adı",
              "promotion_type": "price_drop/installment_increase/contract_offer",
              "description": "Kampanya açıklaması",
              "old_value": "Eski değer",
              "new_value": "Yeni değer",
              "source": "Kampanya kaynağı"
            }
          ]
        }
        ```
        
        Sadece JSON formatında yanıt ver, ekstra açıklama yapma.
        """
        
        # OpenAI API'ye istek gönder
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Sen bir kampanya analisti uzmanısın. Ürün verilerini karşılaştırarak kampanyaları tespit edersin."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        # Sonucu ayrıştır
        content = response.choices[0].message.content
        result = json.loads(content)
        
        return result.get("promotions", [])
    except Exception as e:
        logger.error(f"Kampanya tespiti sırasında hata: {e}")
        return [] 