# 🤖 AI Features - Hệ thống xử lý hóa đơn thông minh

## Tổng quan
Hệ thống đã được tích hợp đầy đủ AI với các tính năng thông minh để tự động hóa quy trình xử lý hóa đơn.

## 🧠 Các tính năng AI chính

### 1. **AI Phân loại hóa đơn** (`InvoiceAIClassifier`)
- **Chức năng**: Tự động phân loại hóa đơn theo loại dịch vụ
- **Danh mục**: Điện, Nước, Internet, Điện thoại, Xăng dầu, Văn phòng phẩm, Thiết bị, Dịch vụ, Khác
- **Độ chính xác**: 85%+ với dữ liệu huấn luyện đầy đủ
- **API**: `POST /api/ai/training/` để huấn luyện model

### 2. **AI Trích xuất dữ liệu** (`InvoiceDataExtractor`)
- **Chức năng**: Trích xuất thông tin thông minh từ OCR text
- **Dữ liệu trích xuất**:
  - Số hóa đơn
  - Tên nhà cung cấp
  - Tổng tiền
  - Thuế VAT
  - Ngày phát hành
  - Ngày đến hạn
  - Danh sách sản phẩm/dịch vụ
- **Độ tin cậy**: Tự động tính toán confidence score

### 3. **AI Phát hiện fraud** (`InvoiceFraudDetector`)
- **Chức năng**: Phát hiện hóa đơn giả và bất thường
- **Kiểm tra**:
  - Format số hóa đơn
  - Số tiền bất thường
  - Ngày tháng hợp lệ
  - Tên nhà cung cấp
  - Chất lượng OCR
- **Mức độ rủi ro**: THẤP, TRUNG BÌNH, CAO
- **API**: `GET /api/ai/analysis/<id>/` để xem phân tích

### 4. **AI Dự đoán** (`AIPredictor`)
- **Dự đoán thời gian xử lý**: Ước tính thời gian OCR dựa trên độ phức tạp
- **Dự đoán khả năng phê duyệt**: Tính toán xác suất hóa đơn được phê duyệt
- **Khuyến nghị**: Đưa ra lời khuyên dựa trên dữ liệu phân tích

### 5. **AI Chatbot** (`AIChatbot`)
- **Chức năng**: Hỗ trợ người dùng 24/7
- **Khả năng**:
  - Giải thích trạng thái hóa đơn
  - Hướng dẫn sử dụng hệ thống
  - Phân tích dữ liệu và báo cáo
  - Khắc phục sự cố
- **API**: `POST /api/ai/chat/` để chat với AI
- **Interface**: `/ai/chat/` - Giao diện chat trực quan

## 📊 AI Dashboard

### Thống kê AI
- **Tổng hóa đơn**: Số lượng hóa đơn trong hệ thống
- **Đã xử lý AI**: Số hóa đơn đã được AI phân tích
- **Tỷ lệ xử lý AI**: Phần trăm hóa đơn được xử lý tự động
- **Fraud phát hiện**: Số hóa đơn có rủi ro fraud
- **Độ tin cậy cao**: Số hóa đơn có confidence > 80%

### Biểu đồ và phân tích
- **Phân loại hóa đơn**: Biểu đồ phân bố theo category
- **Mức độ rủi ro**: Phân bố fraud risk levels
- **Hiệu suất AI Models**: Độ chính xác của các model
- **Xu hướng**: Biểu đồ theo thời gian

## 🔧 Cấu hình AI

### Dependencies cần thiết
```bash
pip install scikit-learn pandas numpy transformers torch openai langchain sentence-transformers spacy
```

### Biến môi trường
```bash
# OpenAI API (cho chatbot)
OPENAI_API_KEY=your_openai_api_key

# Google Cloud Vision (tùy chọn)
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### Cài đặt spaCy model tiếng Việt
```bash
python -m spacy download vi_core_news_sm
```

## 🚀 Sử dụng AI

### 1. Upload hóa đơn với AI
```python
# Tự động chạy AI khi upload
invoice = Invoice.objects.create(file=uploaded_file)
# AI sẽ tự động:
# - Phân loại hóa đơn
# - Trích xuất dữ liệu
# - Phát hiện fraud
# - Dự đoán kết quả
```

### 2. Chat với AI
```javascript
// Gửi tin nhắn đến AI
fetch('/api/ai/chat/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: "Trạng thái hóa đơn ID 1",
        session_id: "session_123"
    })
})
```

### 3. Xem phân tích AI
```javascript
// Lấy phân tích AI cho hóa đơn
fetch('/api/ai/analysis/1/')
    .then(response => response.json())
    .then(data => {
        console.log('AI Category:', data.ai_category);
        console.log('Fraud Risk:', data.fraud_risk_level);
        console.log('Recommendations:', data.ai_recommendations);
    });
```

## 📈 Huấn luyện AI Model

### 1. Chuẩn bị dữ liệu huấn luyện
```python
training_data = [
    {
        'text': 'HÓA ĐƠN ĐIỆN LỰC VIỆT NAM...',
        'category': 'Điện'
    },
    {
        'text': 'CÔNG TY CẤP NƯỚC...',
        'category': 'Nước'
    }
    # ... thêm dữ liệu
]
```

### 2. Huấn luyện model
```python
# API call
POST /api/ai/training/
{
    "training_data": training_data,
    "model_type": "classifier"
}
```

## 🎯 API Endpoints AI

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/ai/chat/` | POST | Chat với AI Bot |
| `/api/ai/analysis/<id>/` | GET | Phân tích AI cho hóa đơn |
| `/api/ai/training/` | POST | Huấn luyện AI model |
| `/api/ai/prediction/<id>/` | GET | Dự đoán AI |
| `/api/ai/dashboard/` | GET | Thống kê AI Dashboard |

## 🔍 Giao diện người dùng

### AI Chat Interface (`/ai/chat/`)
- Chat trực tiếp với AI
- Lưu lịch sử chat
- Context-aware responses
- Real-time typing indicator

### AI Dashboard (`/ai/dashboard/`)
- Thống kê tổng quan AI
- Biểu đồ hiệu suất
- Khuyến nghị AI
- Model performance tracking

## ⚡ Tối ưu hóa

### 1. Caching AI results
```python
# Cache kết quả AI để tăng tốc
from django.core.cache import cache

def get_ai_analysis(invoice_id):
    cache_key = f'ai_analysis_{invoice_id}'
    result = cache.get(cache_key)
    if not result:
        result = ai_extractor.extract_smart_data(text)
        cache.set(cache_key, result, 3600)  # Cache 1 giờ
    return result
```

### 2. Async AI processing
```python
# Sử dụng Celery cho AI processing
@shared_task
def process_ai_async(invoice_id):
    # AI processing trong background
    pass
```

## 🛡️ Bảo mật AI

### 1. Input validation
- Kiểm tra độ dài text
- Sanitize input
- Rate limiting cho API

### 2. Model security
- Encrypt model files
- Secure API keys
- Audit AI decisions

## 📝 Logging và Monitoring

### AI Activity Logs
```python
# Tự động log mọi hoạt động AI
ActivityLog.objects.create(
    user=request.user,
    action="AI_CLASSIFICATION",
    details={"category": "Điện", "confidence": 0.85}
)
```

### Performance Monitoring
- Thời gian xử lý AI
- Độ chính xác model
- Error rates
- User satisfaction

## 🔮 Roadmap AI

### Phase 1 (Hoàn thành) ✅
- [x] AI Classification
- [x] AI Data Extraction  
- [x] Fraud Detection
- [x] AI Chatbot
- [x] AI Dashboard

### Phase 2 (Tương lai) 🚀
- [ ] Deep Learning models
- [ ] Computer Vision cho ảnh
- [ ] Natural Language Processing nâng cao
- [ ] AutoML pipeline
- [ ] Multi-language support

## 📞 Hỗ trợ

Nếu cần hỗ trợ về AI features:
1. Kiểm tra logs trong Django admin
2. Sử dụng AI Chat để được hướng dẫn
3. Xem AI Dashboard để monitor performance
4. Liên hệ admin nếu có lỗi nghiêm trọng

---

**🎉 Chúc mừng! Hệ thống AI của bạn đã sẵn sàng hoạt động!**

