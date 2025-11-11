# D:\...\invoice_processing_system\app_invoices\utils.py

import io
import os 
import re
from datetime import datetime
from PIL import Image
import pytesseract

from django.conf import settings
from google.cloud import vision
from google.oauth2 import service_account

# Khởi tạo Tesseract (Chỉ cần thiết cho Tesseract fallback)
pytesseract.pytesseract.tesseract_cmd = getattr(settings, 'TESSERACT_CMD', '/usr/bin/tesseract')

# Khởi tạo Google Vision Client
def initialize_vision_client():
    """Khởi tạo Google Vision Client từ file credentials."""
    try:
        credentials_path = getattr(settings, 'GOOGLE_VISION_CREDENTIALS', None)
        if not credentials_path or not os.path.exists(credentials_path):
            raise FileNotFoundError("Google Vision credentials file not found.")

        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        return vision.ImageAnnotatorClient(credentials=credentials)
    except Exception as e:
        print(f"Lỗi khởi tạo Vision Client. Tác vụ sẽ chuyển sang Tesseract. Lỗi: {e}")
        return None

vision_client = initialize_vision_client()


# --- HÀM PARSING ---
def parse_invoice_text(text):
    data = {'number': None, 'date': None, 'total': None, 'tax': None}

    # 1. Số hóa đơn
    num_match = re.search(r'(?:SỐ|SỐ HÓA ĐƠN|NO|INVOICE\s*NO)\s*:?\s*([A-Z0-9/-]{3,})', text, re.IGNORECASE)
    if num_match: data['number'] = num_match.group(1).strip()

    # 2. Ngày phát hành
    date_match = re.search(r'(?:Ngày|Date)\s*(?:(\d{1,2})[/-](\d{1,2})[/-](\d{4})|(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4}))', text, re.IGNORECASE)
    if date_match:
        try:
            if date_match.group(3): 
                day, month, year = date_match.group(1), date_match.group(2), date_match.group(3)
            else: 
                day, month, year = date_match.group(4), date_match.group(5), date_match.group(6)
            data['date'] = datetime(int(year), int(month), int(day)).date()
        except (ValueError, TypeError): pass

    # 3. Tổng tiền
    total_match = re.search(r'(?:TỔNG CỘNG TIỀN THANH TOÁN|TỔNG CỘNG|TOTAL):\s*([\d\.,]+)', text, re.IGNORECASE)
    if total_match:
        amount_str = total_match.group(1).replace('.', '').replace(',', '.')
        try: data['total'] = float(amount_str)
        except ValueError: pass

    # 4. Thuế
    tax_match = re.search(r'(?:THUẾ GTGT|VAT):\s*([\d\.,]+)', text, re.IGNORECASE)
    if tax_match:
        amount_str = tax_match.group(1).replace('.', '').replace(',', '.')
        try: data['tax'] = float(amount_str)
        except ValueError: pass
        
    return data

# --- HÀM CHÍNH EXTRACT ---
def extract_invoice_data(file_path):
    """Thực hiện OCR kép (Google Vision -> Tesseract) và Parsing."""
    full_text = ""
    
    # 1. Google Vision (Ưu tiên)
    if vision_client: 
        try:
            with io.open(file_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            response = vision_client.document_text_detection(image=image)
            if response.full_text_annotation:
                full_text = response.full_text_annotation.text
        except Exception:
            pass # Bỏ qua lỗi Vision, chuyển sang Tesseract
            
    # 2. Tesseract (Fallback)
    if not full_text:
        try:
            full_text = pytesseract.image_to_string(Image.open(file_path), lang='vie+eng')
        except Exception:
            return {'number': None, 'date': None, 'total': None, 'tax': None, 'raw_text': ""}

    # 3. Phân tích
    parsed_data = parse_invoice_text(full_text)
    parsed_data['raw_text'] = full_text
    return parsed_data