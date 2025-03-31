import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# API anahtarları
FIRECRAWL_API_KEY = "fc-c5ae03e36e194d5199a6c8744b461ad6"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Google Sheets
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

# E-posta Bildirimleri
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "").split(",")

# Referans Telefon Bilgileri
REFERANS_TELEFON = os.getenv("REFERANS_TELEFON", "Samsung Galaxy A25")
FIYAT_ARALIGI = os.getenv("FIYAT_ARALIĞI", "2000-5000")
MIN_RAM = int(os.getenv("MIN_RAM", "6"))
MIN_DEPOLAMA = int(os.getenv("MIN_DEPOLAMA", "128"))

# Takip Edilecek Siteler
MEDIAMARKT_URL = "https://www.mediamarkt.com.tr/tr/category/android-telefonlar-675172.html"
TEKNOSA_URL = "https://www.teknosa.com/telefon-c-100001002"
VATAN_URL = "https://www.vatanbilgisayar.com/cep-telefonu"
TURKCELL_URL = os.getenv("TURKCELL_URL", "https://www.turkcell.com.tr")
TURKTELEKOM_URL = os.getenv("TURKTELEKOM_URL", "https://www.turktelekom.com.tr")
VODAFONE_URL = os.getenv("VODAFONE_URL", "https://www.vodafone.com.tr")

# Telefon Özellikleri için alanlar
TELEFON_OZELLIKLERI = [
    "Marka",
    "Model",
    "İşlemci",
    "Ekran",
    "RAM",
    "Depolama",
    "Arka Kamera",
    "Ön Kamera",
    "Pil ve Şarj",
    "Ağ Bağlantısı",
    "Lansman Tarihi",
    "Fiyat",
    "Taksit Sayısı",
    "Taksit Tutarı",
    "Peşine Kontrat",
    "Satış Kanalı"
]

# E-ticaret siteleri
ETICARET_SITELERI = {
    "zincir": ["Media Markt", "Teknosa", "Vatan"],
    "operator": ["Turkcell", "Türk Telekom", "Vodafone"]
}

# Rapor zamanı
RAPOR_SAATI = "08:30"

# Supabase ayarları
SUPABASE_URL = 'https://kcuttrlkflvxdqzyekik.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjdXR0cmxrZmx2eGRxenlla2lrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM0MDUzOTksImV4cCI6MjA1ODk4MTM5OX0.cLiM_lxQ95rBsXIt0RwmuYghVcDlU6UjzlyMT2dnWog'

# Uygulama ayarları
DEBUG = bool(os.getenv("DEBUG", True))
PORT = 5004
HOST = '0.0.0.0'

# Veritabanı ayarları
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///telefon_data.db')

# Scraper ayarları
SCRAPER_INTERVAL = 3600  # saniye cinsinden (1 saat)
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Bildirim ayarları
NOTIFICATION_ENABLED = True
EMAIL_ENABLED = False
TELEGRAM_ENABLED = False

# Email ayarları
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
NOTIFICATION_EMAIL = os.getenv('NOTIFICATION_EMAIL', '')

# Telegram ayarları
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Web sunucusu ayarları
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", PORT)) 