# app_invoices/ai_services.py
"""
🤖 AI Services cho hệ thống xử lý hóa đơn
Tích hợp các AI model để phân loại, trích xuất và phân tích hóa đơn thông minh
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# AI Libraries
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from sentence_transformers import SentenceTransformer
    import spacy
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers không được cài đặt. Một số tính năng AI sẽ bị hạn chế.")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI không được cài đặt. Chatbot AI sẽ không hoạt động.")

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class InvoiceAIClassifier:
    """
    🧠 AI Classifier để phân loại hóa đơn tự động
    """
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.categories = [
            'Điện', 'Nước', 'Internet', 'Điện thoại', 'Xăng dầu', 
            'Văn phòng phẩm', 'Thiết bị', 'Dịch vụ', 'Khác'
        ]
        self.model_path = os.path.join(settings.BASE_DIR, 'ai_models', 'invoice_classifier.pkl')
        self.vectorizer_path = os.path.join(settings.BASE_DIR, 'ai_models', 'vectorizer.pkl')
        
    def train_model(self, training_data: List[Dict]):
        """
        🎯 Huấn luyện model phân loại hóa đơn
        """
        try:
            # Chuẩn bị dữ liệu
            texts = [item['text'] for item in training_data]
            labels = [item['category'] for item in training_data]
            
            # Vectorize text
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words=None,  # Giữ lại stop words tiếng Việt
                ngram_range=(1, 3)
            )
            X = self.vectorizer.fit_transform(texts)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            self.model.fit(X, labels)
            
            # Lưu model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.vectorizer, self.vectorizer_path)
            
            logger.info("✅ AI Classifier đã được huấn luyện thành công")
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi huấn luyện AI Classifier: {e}")
            return False
    
    def load_model(self):
        """
        📥 Load model đã huấn luyện
        """
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Lỗi load AI model: {e}")
            return False
    
    def classify_invoice(self, ocr_text: str) -> Dict:
        """
        🔍 Phân loại hóa đơn dựa trên OCR text
        """
        try:
            if not self.model or not self.vectorizer:
                if not self.load_model():
                    return {
                        'category': 'Khác',
                        'confidence': 0.0,
                        'reason': 'Model chưa được huấn luyện'
                    }
            
            # Vectorize text
            X = self.vectorizer.transform([ocr_text])
            
            # Predict
            prediction = self.model.predict(X)[0]
            confidence = max(self.model.predict_proba(X)[0])
            
            return {
                'category': prediction,
                'confidence': float(confidence),
                'reason': f'Phân loại dựa trên từ khóa: {self._extract_keywords(ocr_text)}'
            }
            
        except Exception as e:
            logger.error(f"❌ Lỗi phân loại hóa đơn: {e}")
            return {
                'category': 'Khác',
                'confidence': 0.0,
                'reason': f'Lỗi AI: {str(e)}'
            }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        🔑 Trích xuất từ khóa quan trọng
        """
        keywords = []
        text_lower = text.lower()
        
        # Từ khóa điện
        if any(word in text_lower for word in ['điện', 'electric', 'evn', 'đèn']):
            keywords.append('điện')
        
        # Từ khóa nước
        if any(word in text_lower for word in ['nước', 'water', 'cấp nước']):
            keywords.append('nước')
            
        # Từ khóa internet
        if any(word in text_lower for word in ['internet', 'wifi', 'mạng', 'fpt', 'viettel']):
            keywords.append('internet')
            
        return keywords[:3]  # Trả về tối đa 3 từ khóa


class InvoiceDataExtractor:
    """
    🔍 AI Data Extractor để trích xuất thông tin thông minh
    """
    
    def __init__(self):
        self.nlp = None
        if TRANSFORMERS_AVAILABLE:
            try:
                # Load Vietnamese NLP model
                self.nlp = spacy.load("vi_core_news_sm")
            except OSError:
                logger.warning("⚠️ Không tìm thấy model tiếng Việt cho spaCy")
    
    def extract_smart_data(self, ocr_text: str) -> Dict:
        """
        🧠 Trích xuất dữ liệu thông minh từ OCR text
        """
        try:
            extracted = {
                'invoice_number': self._extract_invoice_number(ocr_text),
                'supplier_name': self._extract_supplier_name(ocr_text),
                'total_amount': self._extract_total_amount(ocr_text),
                'tax_amount': self._extract_tax_amount(ocr_text),
                'issue_date': self._extract_date(ocr_text),
                'due_date': self._extract_due_date(ocr_text),
                'items': self._extract_items(ocr_text),
                'confidence_score': 0.0
            }
            
            # Tính confidence score
            extracted['confidence_score'] = self._calculate_confidence(extracted)
            
            return extracted
            
        except Exception as e:
            logger.error(f"❌ Lỗi trích xuất dữ liệu AI: {e}")
            return {}
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """
        🔢 Trích xuất số hóa đơn thông minh
        """
        patterns = [
            r'(?:Số|No|Number)[\s:]*(\d{4,10})',
            r'(?:Hóa đơn|Invoice)[\s:]*(\d{4,10})',
            r'(\d{4,10})(?=\s*(?:ngày|date|tháng))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_supplier_name(self, text: str) -> Optional[str]:
        """
        🏢 Trích xuất tên nhà cung cấp thông minh
        """
        # Tìm tên công ty
        company_patterns = [
            r'(?:Công ty|Company|Corp|Ltd)[\s:]*([A-Za-zÀ-ỹ\s&]+)',
            r'([A-Z][A-Za-zÀ-ỹ\s&]+(?:JSC|Ltd|Corp|Company))',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # Fallback: tìm dòng đầu tiên có thể là tên công ty
        lines = text.split('\n')[:5]  # 5 dòng đầu
        for line in lines:
            if len(line) > 10 and any(char.isupper() for char in line):
                return line.strip()
        
        return None
    
    def _extract_total_amount(self, text: str) -> Optional[float]:
        """
        💰 Trích xuất tổng tiền thông minh
        """
        # Patterns cho tổng tiền
        patterns = [
            r'(?:Tổng|Total|Tổng cộng)[\s:]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*(?:đ|VND|₫)',
            r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)(?=\s*(?:đ|VND|₫))',
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean và convert
                    clean_amount = match.replace('.', '').replace(',', '.')
                    amount = float(clean_amount)
                    if amount > 1000:  # Chỉ lấy số tiền hợp lý
                        amounts.append(amount)
                except:
                    continue
        
        # Trả về số tiền lớn nhất (thường là tổng)
        return max(amounts) if amounts else None
    
    def _extract_tax_amount(self, text: str) -> Optional[float]:
        """
        🧾 Trích xuất thuế VAT
        """
        patterns = [
            r'(?:VAT|Thuế|Tax)[\s:]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
            r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*(?:đ|VND|₫)(?=\s*(?:VAT|Thuế))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    clean_amount = match.group(1).replace('.', '').replace(',', '.')
                    return float(clean_amount)
                except:
                    continue
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """
        📅 Trích xuất ngày phát hành
        """
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}\s+(?:tháng|month)\s+\d{4})',
            r'(?:Ngày|Date)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """
        ⏰ Trích xuất ngày đến hạn
        """
        patterns = [
            r'(?:Hạn thanh toán|Due date|Đến hạn)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})(?=\s*(?:hạn|due))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_items(self, text: str) -> List[Dict]:
        """
        📦 Trích xuất danh sách sản phẩm/dịch vụ
        """
        items = []
        lines = text.split('\n')
        
        for line in lines:
            # Tìm dòng có số lượng, tên sản phẩm, giá
            if re.search(r'\d+\s+[A-Za-zÀ-ỹ]+\s+\d+', line):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        quantity = int(parts[0])
                        price = float(parts[-1].replace(',', '.'))
                        name = ' '.join(parts[1:-1])
                        
                        items.append({
                            'name': name,
                            'quantity': quantity,
                            'price': price,
                            'total': quantity * price
                        })
                    except:
                        continue
        
        return items[:10]  # Tối đa 10 items
    
    def _calculate_confidence(self, extracted: Dict) -> float:
        """
        📊 Tính độ tin cậy của dữ liệu trích xuất
        """
        score = 0.0
        total_fields = 6
        
        if extracted.get('invoice_number'):
            score += 1.0
        if extracted.get('supplier_name'):
            score += 1.0
        if extracted.get('total_amount'):
            score += 1.0
        if extracted.get('issue_date'):
            score += 1.0
        if extracted.get('items'):
            score += 1.0
        if extracted.get('tax_amount'):
            score += 0.5  # Thuế là optional
            
        return round(score / total_fields, 2)


class InvoiceFraudDetector:
    """
    🕵️ AI Fraud Detector để phát hiện hóa đơn giả/lỗi
    """
    
    def __init__(self):
        self.anomaly_threshold = 0.7
        
    def detect_fraud(self, invoice_data: Dict, ocr_text: str) -> Dict:
        """
        🔍 Phát hiện hóa đơn giả/lỗi
        """
        try:
            fraud_indicators = []
            risk_score = 0.0
            
            # 1. Kiểm tra format số hóa đơn
            if not self._validate_invoice_number(invoice_data.get('invoice_number', '')):
                fraud_indicators.append("Số hóa đơn không hợp lệ")
                risk_score += 0.2
            
            # 2. Kiểm tra tổng tiền bất thường
            if not self._validate_amount(invoice_data.get('total_amount', 0)):
                fraud_indicators.append("Số tiền bất thường")
                risk_score += 0.3
            
            # 3. Kiểm tra ngày tháng
            if not self._validate_dates(invoice_data):
                fraud_indicators.append("Ngày tháng không hợp lệ")
                risk_score += 0.2
            
            # 4. Kiểm tra tên nhà cung cấp
            if not self._validate_supplier(invoice_data.get('supplier_name', '')):
                fraud_indicators.append("Tên nhà cung cấp không hợp lệ")
                risk_score += 0.1
            
            # 5. Kiểm tra độ mờ/khó đọc của OCR
            if self._check_ocr_quality(ocr_text):
                fraud_indicators.append("Chất lượng ảnh kém, có thể là giả")
                risk_score += 0.2
            
            # Xác định mức độ rủi ro
            if risk_score >= 0.8:
                risk_level = "CAO"
            elif risk_score >= 0.5:
                risk_level = "TRUNG BÌNH"
            else:
                risk_level = "THẤP"
            
            return {
                'is_fraud': risk_score >= self.anomaly_threshold,
                'risk_score': round(risk_score, 2),
                'risk_level': risk_level,
                'indicators': fraud_indicators,
                'recommendation': self._get_recommendation(risk_score)
            }
            
        except Exception as e:
            logger.error(f"❌ Lỗi phát hiện fraud: {e}")
            return {
                'is_fraud': False,
                'risk_score': 0.0,
                'risk_level': 'THẤP',
                'indicators': [],
                'recommendation': 'Không thể phân tích'
            }
    
    def _validate_invoice_number(self, invoice_number: str) -> bool:
        """Kiểm tra format số hóa đơn"""
        if not invoice_number:
            return False
        return len(invoice_number) >= 4 and invoice_number.isdigit()
    
    def _validate_amount(self, amount: float) -> bool:
        """Kiểm tra số tiền hợp lý"""
        if not amount:
            return False
        return 1000 <= amount <= 1000000000  # 1K - 1B VND
    
    def _validate_dates(self, invoice_data: Dict) -> bool:
        """Kiểm tra ngày tháng hợp lý"""
        try:
            issue_date = invoice_data.get('issue_date')
            if not issue_date:
                return True  # Không có ngày thì không kiểm tra
            
            # Parse date và kiểm tra
            if '/' in issue_date:
                day, month, year = issue_date.split('/')
                date_obj = datetime(int(year), int(month), int(day))
                
                # Kiểm tra ngày không quá xa trong tương lai
                now = datetime.now()
                if date_obj > now:
                    return False
                    
                # Kiểm tra không quá cũ (2 năm)
                if (now - date_obj).days > 730:
                    return False
                    
            return True
        except:
            return False
    
    def _validate_supplier(self, supplier_name: str) -> bool:
        """Kiểm tra tên nhà cung cấp hợp lệ"""
        if not supplier_name:
            return False
        
        # Kiểm tra độ dài và ký tự
        if len(supplier_name) < 3 or len(supplier_name) > 100:
            return False
            
        # Kiểm tra có chứa ký tự đặc biệt bất thường
        if re.search(r'[^\w\sÀ-ỹ&.,-]', supplier_name):
            return False
            
        return True
    
    def _check_ocr_quality(self, ocr_text: str) -> bool:
        """Kiểm tra chất lượng OCR"""
        if not ocr_text or len(ocr_text) < 50:
            return True  # Chất lượng kém
        
        # Kiểm tra tỷ lệ ký tự đặc biệt
        special_chars = len(re.findall(r'[^\w\sÀ-ỹ]', ocr_text))
        total_chars = len(ocr_text)
        
        if total_chars > 0 and special_chars / total_chars > 0.3:
            return True  # Quá nhiều ký tự đặc biệt
        
        return False
    
    def _get_recommendation(self, risk_score: float) -> str:
        """Đưa ra khuyến nghị dựa trên risk score"""
        if risk_score >= 0.8:
            return "🚨 CẦN KIỂM TRA THỦ CÔNG - Rủi ro cao"
        elif risk_score >= 0.5:
            return "⚠️ CẦN XEM XÉT - Rủi ro trung bình"
        else:
            return "✅ AN TOÀN - Có thể xử lý tự động"


class AIChatbot:
    """
    🤖 AI Chatbot hỗ trợ người dùng
    """
    
    def __init__(self):
        self.openai_available = OPENAI_AVAILABLE
        if self.openai_available:
            try:
                openai.api_key = os.getenv('OPENAI_API_KEY')
            except:
                self.openai_available = False
    
    def chat(self, user_message: str, context: Dict = None) -> str:
        """
        💬 Chat với AI bot
        """
        try:
            if not self.openai_available:
                return self._fallback_response(user_message)
            
            # Tạo prompt context
            system_prompt = """
            Bạn là AI assistant chuyên về xử lý hóa đơn. 
            Bạn có thể giúp:
            - Giải thích trạng thái hóa đơn
            - Hướng dẫn sử dụng hệ thống
            - Phân tích dữ liệu hóa đơn
            - Đưa ra khuyến nghị
            """
            
            if context:
                system_prompt += f"\nContext hiện tại: {json.dumps(context, ensure_ascii=False)}"
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ Lỗi AI Chatbot: {e}")
            return self._fallback_response(user_message)
    
    def _fallback_response(self, user_message: str) -> str:
        """
        🔄 Fallback response khi không có OpenAI
        """
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['trạng thái', 'status', 'hóa đơn']):
            return "Trạng thái hóa đơn có thể là: Đã tải lên, Đang xử lý OCR, Đã xử lý OCR, Chờ xem xét, Đã khớp, Sai lệch, Chờ phê duyệt, Lỗi tích hợp ERP, Bị từ chối, Đã phê duyệt."
        
        elif any(word in message_lower for word in ['hướng dẫn', 'help', 'giúp']):
            return "Tôi có thể giúp bạn: 1) Upload hóa đơn 2) Xem trạng thái xử lý 3) Phê duyệt hóa đơn 4) Xem báo cáo. Bạn cần hỗ trợ gì cụ thể?"
        
        elif any(word in message_lower for word in ['lỗi', 'error', 'không hoạt động']):
            return "Nếu gặp lỗi, hãy kiểm tra: 1) File ảnh có rõ nét không 2) Kết nối mạng 3) Thử upload lại. Nếu vẫn lỗi, liên hệ admin."
        
        else:
            return "Xin chào! Tôi là AI assistant của hệ thống xử lý hóa đơn. Tôi có thể giúp bạn về trạng thái hóa đơn, hướng dẫn sử dụng, hoặc phân tích dữ liệu. Bạn cần hỗ trợ gì?"


class AIPredictor:
    """
    🔮 AI Predictor để dự đoán và cảnh báo
    """
    
    def __init__(self):
        self.prediction_model = None
    
    def predict_invoice_processing_time(self, invoice_data: Dict) -> Dict:
        """
        ⏱️ Dự đoán thời gian xử lý hóa đơn
        """
        try:
            # Các yếu tố ảnh hưởng đến thời gian xử lý
            factors = {
                'text_length': len(invoice_data.get('raw_ocr_text', '')),
                'has_invoice_number': bool(invoice_data.get('invoice_number')),
                'has_supplier': bool(invoice_data.get('supplier_name')),
                'has_amount': bool(invoice_data.get('total_amount')),
                'image_quality': self._estimate_image_quality(invoice_data.get('raw_ocr_text', ''))
            }
            
            # Tính toán thời gian dự đoán (giây)
            base_time = 30  # 30 giây cơ bản
            
            if factors['text_length'] > 1000:
                base_time += 20
            if not factors['has_invoice_number']:
                base_time += 15
            if not factors['has_supplier']:
                base_time += 10
            if factors['image_quality'] < 0.7:
                base_time += 25
            
            return {
                'predicted_time': base_time,
                'confidence': 0.8,
                'factors': factors,
                'recommendation': self._get_processing_recommendation(factors)
            }
            
        except Exception as e:
            logger.error(f"❌ Lỗi dự đoán thời gian: {e}")
            return {'predicted_time': 60, 'confidence': 0.5}
    
    def predict_invoice_approval_probability(self, invoice_data: Dict) -> Dict:
        """
        📊 Dự đoán khả năng phê duyệt hóa đơn
        """
        try:
            score = 0.0
            factors = []
            
            # Kiểm tra các yếu tố tích cực
            if invoice_data.get('invoice_number'):
                score += 0.3
                factors.append("Có số hóa đơn")
            
            if invoice_data.get('supplier_name'):
                score += 0.2
                factors.append("Có tên nhà cung cấp")
            
            if invoice_data.get('total_amount') and invoice_data['total_amount'] > 0:
                score += 0.3
                factors.append("Có số tiền hợp lệ")
            
            if invoice_data.get('issue_date'):
                score += 0.1
                factors.append("Có ngày phát hành")
            
            # Kiểm tra yếu tố tiêu cực
            if not invoice_data.get('raw_ocr_text') or len(invoice_data['raw_ocr_text']) < 100:
                score -= 0.2
                factors.append("OCR text quá ngắn")
            
            # Đảm bảo score trong khoảng 0-1
            score = max(0, min(1, score))
            
            return {
                'approval_probability': round(score, 2),
                'confidence': 0.75,
                'factors': factors,
                'recommendation': self._get_approval_recommendation(score)
            }
            
        except Exception as e:
            logger.error(f"❌ Lỗi dự đoán phê duyệt: {e}")
            return {'approval_probability': 0.5, 'confidence': 0.5}
    
    def _estimate_image_quality(self, ocr_text: str) -> float:
        """Ước tính chất lượng ảnh dựa trên OCR text"""
        if not ocr_text:
            return 0.0
        
        # Các chỉ số chất lượng
        text_length = len(ocr_text)
        word_count = len(ocr_text.split())
        special_char_ratio = len(re.findall(r'[^\w\sÀ-ỹ]', ocr_text)) / text_length if text_length > 0 else 0
        
        # Tính điểm chất lượng (0-1)
        quality_score = 1.0
        
        if text_length < 100:
            quality_score -= 0.3
        if word_count < 20:
            quality_score -= 0.2
        if special_char_ratio > 0.3:
            quality_score -= 0.3
        
        return max(0, min(1, quality_score))
    
    def _get_processing_recommendation(self, factors: Dict) -> str:
        """Đưa ra khuyến nghị xử lý"""
        if factors['image_quality'] < 0.5:
            return "⚠️ Chất lượng ảnh kém, cần upload lại ảnh rõ nét hơn"
        elif not factors['has_invoice_number']:
            return "📝 Thiếu số hóa đơn, cần kiểm tra thủ công"
        elif not factors['has_supplier']:
            return "🏢 Thiếu tên nhà cung cấp, cần bổ sung thông tin"
        else:
            return "✅ Hóa đơn có thể xử lý tự động"
    
    def _get_approval_recommendation(self, probability: float) -> str:
        """Đưa ra khuyến nghị phê duyệt"""
        if probability >= 0.8:
            return "✅ Có thể phê duyệt tự động"
        elif probability >= 0.6:
            return "⚠️ Cần kiểm tra nhanh trước khi phê duyệt"
        else:
            return "🔍 Cần kiểm tra kỹ lưỡng trước khi phê duyệt"


# Global AI Services Instances
ai_classifier = InvoiceAIClassifier()
ai_extractor = InvoiceDataExtractor()
fraud_detector = InvoiceFraudDetector()
ai_chatbot = AIChatbot()
ai_predictor = AIPredictor()

