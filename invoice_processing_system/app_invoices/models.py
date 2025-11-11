# app_invoices/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    # ... Thêm các trường khác của Supplier
    
    def __str__(self):
        return self.name

class InvoiceStatus(models.TextChoices):
    UPLOADED = 'UPLOADED', _('Đã tải lên')
    OCR_PROCESSING = 'OCR_PROCESSING', _('Đang xử lý OCR')
    OCR_PROCESSED = 'OCR_PROCESSED', _('Đã xử lý OCR')
    PENDING_REVIEW = 'PENDING_REVIEW', _('Chờ xem xét')
    MATCHED = 'MATCHED', _('Đã khớp')
    UNMATCHED = 'UNMATCHED', _('Sai lệch')
    PENDING_APPROVAL = 'PENDING_APPROVAL', _('Chờ phê duyệt')
    INTEGRATION_ERROR = 'INTEGRATION_ERROR', _('Lỗi tích hợp ERP')
    REJECTED = 'REJECTED', _('Bị từ chối')
    APPROVED = 'APPROVED', _('Đã phê duyệt')

class Invoice(models.Model):
    file = models.FileField(upload_to='invoices/')
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=InvoiceStatus.choices, default=InvoiceStatus.UPLOADED)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # OCR and Matching Metadata
    raw_ocr_text = models.TextField(blank=True)
    ocr_start_time = models.DateTimeField(null=True, blank=True)
    ocr_end_time = models.DateTimeField(null=True, blank=True)
    match_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    is_invoice = models.BooleanField(default=False)
    
    # 🤖 AI Fields
    ai_category = models.CharField(max_length=100, blank=True, null=True, help_text="Phân loại AI")
    ai_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Độ tin cậy AI")
    fraud_risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Điểm rủi ro fraud")
    fraud_risk_level = models.CharField(max_length=20, blank=True, null=True, help_text="Mức độ rủi ro")
    ai_extracted_data = models.JSONField(blank=True, null=True, help_text="Dữ liệu AI trích xuất")
    ai_processing_time = models.IntegerField(null=True, blank=True, help_text="Thời gian xử lý AI (giây)")
    ai_recommendations = models.TextField(blank=True, help_text="Khuyến nghị AI")
    
    def __str__(self):
        return self.invoice_number or f"Invoice {self.id}"

class ExtractedField(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='extracted_fields', on_delete=models.CASCADE)
    field_name = models.CharField(max_length=100)
    extracted_value = models.TextField()
    confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
class TaskAssignment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    task_type = models.CharField(max_length=50) 
    status = models.CharField(max_length=50, default='PENDING')
    due_date = models.DateTimeField()
    
class ERPIntegrationConfig(models.Model):
    system_name = models.CharField(max_length=100, unique=True)
    api_url = models.URLField()
    api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

class MatchingRule(models.Model):
    priority = models.IntegerField(unique=True)
    rule_logic = models.TextField() 
    is_active = models.BooleanField(default=True)

class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

# 🤖 AI Models
class AIChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"AI Chat Session {self.session_id}"

class AIChatMessage(models.Model):
    session = models.ForeignKey(AIChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=[
        ('user', 'Người dùng'),
        ('ai', 'AI Bot'),
        ('system', 'Hệ thống')
    ])
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    context = models.JSONField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

class AIModelTraining(models.Model):
    model_name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, choices=[
        ('classifier', 'Phân loại'),
        ('extractor', 'Trích xuất'),
        ('fraud_detector', 'Phát hiện fraud'),
        ('predictor', 'Dự đoán')
    ])
    training_data_count = models.IntegerField(default=0)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    last_trained = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    model_file_path = models.CharField(max_length=500, blank=True)
    
    def __str__(self):
        return f"{self.model_name} ({self.model_type})"

class AIRecommendation(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, null=True, blank=True)
    recommendation_type = models.CharField(max_length=50, choices=[
        ('approval', 'Phê duyệt'),
        ('review', 'Xem xét'),
        ('reject', 'Từ chối'),
        ('manual_check', 'Kiểm tra thủ công')
    ])
    confidence = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"AI Recommendation: {self.recommendation_type}"
    
    