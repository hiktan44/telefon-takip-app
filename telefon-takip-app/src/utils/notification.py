import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import os
import pandas as pd
from io import BytesIO
from datetime import datetime
import sys

# Ana dizini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS

logger = logging.getLogger(__name__)

def send_email_notification(subject, message, attachments=None):
    """
    E-posta bildirimi gönderir.
    
    Args:
        subject (str): E-posta konusu
        message (str): E-posta mesajı (HTML formatında)
        attachments (list, optional): Ekleri içeren liste. Her öğe (dosya_adı, dosya_içeriği, mime_tipi) formatında olmalı.
        
    Returns:
        bool: Gönderim başarılı ise True, değilse False
    """
    try:
        if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENTS]):
            logger.error("E-posta ayarları tamamlanmamış")
            return False
            
        # E-posta mesajını oluştur
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = ', '.join(EMAIL_RECIPIENTS)
        
        # HTML içeriğini ekle
        html_part = MIMEText(message, 'html')
        msg.attach(html_part)
        
        # Ekleri ekle
        if attachments:
            for attachment in attachments:
                filename, content, mimetype = attachment
                
                if mimetype.startswith('image/'):
                    # Görsel eklentisi
                    img = MIMEImage(content)
                    img.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(img)
                else:
                    # Dosya eklentisi
                    part = MIMEApplication(content)
                    part.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(part)
        
        # E-postayı gönder
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())
            
        logger.info(f"E-posta gönderildi: {subject}")
        return True
    except Exception as e:
        logger.error(f"E-posta gönderilirken hata: {e}")
        return False

def send_daily_report(phones_data, promotions=None):
    """
    Günlük telefon karşılaştırma raporunu gönderir.
    
    Args:
        phones_data (list): Telefon verilerinin listesi
        promotions (list, optional): Tespit edilen kampanyaların listesi
        
    Returns:
        bool: Gönderim başarılı ise True, değilse False
    """
    try:
        today = datetime.now().strftime("%d.%m.%Y")
        subject = f"Günlük Telefon Karşılaştırma Raporu - {today}"
        
        # Excel dosyası oluştur
        excel_buffer = BytesIO()
        
        # Veriyi DataFrame'e dönüştür
        df = pd.DataFrame(phones_data)
        
        # Excel'e kaydet
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name="Telefon Karşılaştırma", index=False)
            
            # Formatlama için workbook ve worksheet
            workbook = writer.book
            worksheet = writer.sheets["Telefon Karşılaştırma"]
            
            # Başlık formatı
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Başlıkları formatla
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Sütun genişliklerini ayarla
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
        
        excel_buffer.seek(0)
        excel_data = excel_buffer.getvalue()
        
        # HTML mesajı oluştur
        html_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .promotion {{ color: #e74c3c; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Günlük Telefon Karşılaştırma Raporu - {today}</h1>
            <p>Toplam <b>{len(phones_data)}</b> telefon karşılaştırıldı.</p>
        """
        
        # Kampanyaları ekle
        if promotions and len(promotions) > 0:
            html_message += """
            <h2>Tespit Edilen Kampanyalar</h2>
            <table>
                <tr>
                    <th>Telefon</th>
                    <th>Kampanya Türü</th>
                    <th>Açıklama</th>
                    <th>Eski Değer</th>
                    <th>Yeni Değer</th>
                    <th>Kaynak</th>
                </tr>
            """
            
            for promo in promotions:
                html_message += f"""
                <tr class="promotion">
                    <td>{promo.get('phone_name', '')}</td>
                    <td>{promo.get('promotion_type', '').replace('_', ' ').title()}</td>
                    <td>{promo.get('description', '')}</td>
                    <td>{promo.get('old_value', '')}</td>
                    <td>{promo.get('new_value', '')}</td>
                    <td>{promo.get('source', '')}</td>
                </tr>
                """
                
            html_message += "</table>"
        
        html_message += """
            <p>Detaylı rapor için ekteki Excel dosyasını inceleyebilirsiniz.</p>
            <p>Bu rapor otomatik olarak oluşturulmuştur.</p>
        </body>
        </html>
        """
        
        # E-postayı gönder
        attachments = [
            (f"telefon_raporu_{today.replace('.', '_')}.xlsx", excel_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        ]
        
        return send_email_notification(subject, html_message, attachments)
    except Exception as e:
        logger.error(f"Günlük rapor gönderilirken hata: {e}")
        return False

def send_promotion_alert(promotion):
    """
    Yeni bir kampanya tespit edildiğinde bildirim gönderir.
    
    Args:
        promotion (dict): Kampanya bilgileri
        
    Returns:
        bool: Gönderim başarılı ise True, değilse False
    """
    try:
        if not promotion:
            return False
            
        phone_name = promotion.get('phone_name', '')
        promotion_type = promotion.get('promotion_type', '').replace('_', ' ').title()
        
        subject = f"Yeni Kampanya Bildirimi: {phone_name} - {promotion_type}"
        
        html_message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1 {{ color: #c0392b; }}
                .promotion {{ background-color: #f9f9f9; padding: 15px; border-left: 5px solid #e74c3c; }}
                .highlight {{ color: #e74c3c; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1>Yeni Kampanya Bildirimi</h1>
            <div class="promotion">
                <h2>{phone_name}</h2>
                <p><b>Kampanya Türü:</b> {promotion_type}</p>
                <p><b>Açıklama:</b> {promotion.get('description', '')}</p>
                <p><b>Eski Değer:</b> {promotion.get('old_value', '')}</p>
                <p><b>Yeni Değer:</b> <span class="highlight">{promotion.get('new_value', '')}</span></p>
                <p><b>Kaynak:</b> {promotion.get('source', '')}</p>
            </div>
            <p>Bu bildirim otomatik olarak oluşturulmuştur.</p>
        </body>
        </html>
        """
        
        return send_email_notification(subject, html_message)
    except Exception as e:
        logger.error(f"Kampanya bildirimi gönderilirken hata: {e}")
        return False 