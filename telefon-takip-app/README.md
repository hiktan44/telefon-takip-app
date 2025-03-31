# Telefon Karşılaştırma Uygulaması

Bu uygulama, mobil telefon rakiplerinin fiyatlarını ve kampanyalarını takip etmek için geliştirilmiş bir araçtır. Belirtilen özelliklere en yakın, satış rakamları ilk beşte yer alan beş markanın benzer ürünlerini otomatik olarak takip eder ve günlük raporlar oluşturur.

## Özellikler

- Belirlenen kaynaklardan telefon verilerini otomatik toplama
- En benzer özelliklere sahip telefonları bulma
- Günlük fiyat ve kampanya takibi
- Google Sheets entegrasyonu ile karşılaştırma tablosu oluşturma
- Otomatik bildirimler ve raporlar

## Kurulum

1. Gerekli paketleri yükleyin:
   ```
   pip install -r requirements.txt
   ```

2. `.env` dosyasını oluşturun ve gerekli API anahtarlarını ekleyin:
   ```
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

3. Google Sheets API için credentials.json dosyasını `data` klasörüne ekleyin.

## Kullanım

Uygulamayı başlatmak için:

```
python src/main.py
```

## Özellik Detayları

- Rakip ürünlerin telefon özellikleri: İşlemci, Ekran, RAM+ROM, Arka Kamera, Ön Kamera, Pil ve Şarj, Fiyat, Ağ bağlantısı, Lansman Tarihi
- Zincir kanalda (Media Markt, Teknosa, Vatan) ve Operatör'de (Turkcell, Turk Telekom, Avea) güncel fiyatlar
- Taksit sayısı, taksit tutarı ve peşine kontrat bilgileri
- Özellik bazlı sıralama
- Online kanallarda rakip telefonların genel yorumları ve puanlaması

## Bakım ve Destek

Günlük rapor saat 08:30'da otomatik olarak oluşturulur ve bildirim gönderilir. 