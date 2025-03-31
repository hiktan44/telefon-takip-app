import pandas as pd
import xlsxwriter
import logging
import os
from datetime import datetime
import json

def export_to_excel(data, filename=None):
    """
    Telefon karşılaştırma verilerini Excel formatında dışa aktarır.
    
    Args:
        data (list): Telefon verilerinin listesi
        filename (str, optional): Dosya adı. Belirtilmezse timestamp ile oluşturulur.
    
    Returns:
        str: Oluşturulan dosyanın yolu
    """
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"telefon_karsilastirma_{timestamp}.xlsx"
        
        # Klasör oluştur
        os.makedirs('exports', exist_ok=True)
        file_path = os.path.join('exports', filename)
        
        # DataFrame oluştur
        df = pd.DataFrame(data)
        
        # Excel dosyasını oluştur
        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Karşılaştırma', index=False)
        
        # Excel formatlaması
        workbook = writer.book
        worksheet = writer.sheets['Karşılaştırma']
        
        # Format oluştur
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Başlık formatlaması
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Sütun genişliklerini ayarla
        for i, col in enumerate(df.columns):
            column_width = max(df[col].astype(str).map(len).max(), len(col) + 2)
            worksheet.set_column(i, i, column_width)
        
        writer.close()
        logging.info(f"Excel dosyası oluşturuldu: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Excel export hatası: {str(e)}")
        return None

def export_to_html(data, filename=None):
    """
    Telefon karşılaştırma verilerini HTML formatında dışa aktarır.
    
    Args:
        data (list): Telefon verilerinin listesi
        filename (str, optional): Dosya adı. Belirtilmezse timestamp ile oluşturulur.
    
    Returns:
        str: Oluşturulan dosyanın yolu
    """
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"telefon_karsilastirma_{timestamp}.html"
        
        # Klasör oluştur
        os.makedirs('exports', exist_ok=True)
        file_path = os.path.join('exports', filename)
        
        # DataFrame oluştur
        df = pd.DataFrame(data)
        
        # HTML template
        html_template = """
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Telefon Karşılaştırma Raporu</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #2c3e50;
                    text-align: center;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                    color: #333;
                }
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                tr:hover {
                    background-color: #f1f1f1;
                }
                .footer {
                    margin-top: 30px;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 0.8em;
                }
            </style>
        </head>
        <body>
            <h1>Telefon Karşılaştırma Raporu</h1>
            <p>Oluşturulma tarihi: {datetime}</p>
            {table_html}
            <div class="footer">
                <p>Bu rapor Telefon Takip uygulaması tarafından otomatik olarak oluşturulmuştur.</p>
            </div>
        </body>
        </html>
        """
        
        # HTML tablosunu oluştur
        table_html = df.to_html(index=False, classes="table table-striped table-hover")
        
        # Template'i doldur
        html_content = html_template.format(
            datetime=datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            table_html=table_html
        )
        
        # HTML dosyasını kaydet
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"HTML raporu oluşturuldu: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"HTML export hatası: {str(e)}")
        return None 