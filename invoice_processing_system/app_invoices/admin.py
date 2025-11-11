# app_invoices/admin.py (HOÀN CHỈNH)

import os
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Invoice, ExtractedField, Supplier, ERPIntegrationConfig, 
    MatchingRule, TaskAssignment, ActivityLog, InvoiceStatus
)

# Inline cho phép hiển thị ExtractedField trong trang Invoice Admin
class ExtractedFieldInline(admin.TabularInline):
    model = ExtractedField
    extra = 0
    # Các trường này chỉ để đọc trong Admin
    readonly_fields = ('field_name', 'extracted_value', 'confidence', 'is_verified')
    can_delete = False

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    # --- ĐỊNH NGHĨA CÁC PHƯƠNG THỨC BỊ THIẾU (FIX E035, E108) ---
    
    def original_filename(self, obj):
        """Hiển thị tên file gốc từ FileField."""
        if obj.file:
            # os.path.basename chỉ lấy tên file cuối cùng
            return os.path.basename(obj.file.name)
        return "N/A"
    original_filename.short_description = "Tên File Gốc"
    original_filename.admin_order_field = 'file'

    def processing_duration(self, obj):
        """Tính toán và hiển thị thời gian xử lý OCR."""
        # Yêu cầu Invoice model phải có ocr_start_time và ocr_end_time
        if obj.ocr_start_time and obj.ocr_end_time:
            duration = obj.ocr_end_time - obj.ocr_start_time
            total_seconds = duration.total_seconds()
            # Định dạng thành chuỗi X.XX giây
            return f"{total_seconds:.2f}s"
        elif obj.status == InvoiceStatus.OCR_PROCESSING:
            return "Đang xử lý..."
        return "N/A"
    processing_duration.short_description = "Thời gian OCR" # FIX E108

    # --- CẤU HÌNH ADMIN ---
    
    list_display = [
        'id', 'invoice_number', 'supplier', 'status', 'total_amount', 
        'processing_duration', # SỬA LỖI: Gọi phương thức vừa định nghĩa
        'uploaded_at', 'uploaded_by'
    ]
    
    list_filter = ['status', 'supplier', 'uploaded_at']
    search_fields = ['invoice_number', 'supplier__name', 'raw_ocr_text']
    raw_id_fields = ['supplier', 'uploaded_by']

    fieldsets = (
        ("Thông tin cơ bản", {
            'fields': ('file', 'invoice_number', 'supplier', 'total_amount', 'status', 'uploaded_by'),
        }),
        ("Dữ liệu OCR thô", {
            'fields': ('raw_ocr_text',),
            'classes': ('collapse',),
        }),
        ("Metadata & Theo dõi", {
            'fields': (
                'ocr_start_time', 'ocr_end_time', 'match_score', 
                'original_filename',      # SỬA LỖI: Gọi phương thức
                'processing_duration',    # SỬA LỖI: Gọi phương thức
                'uploaded_at'
            ),
            'description': "Thông tin về quá trình xử lý tự động và tên file gốc."
        }),
    )

    # Các trường chỉ cho phép đọc trong giao diện chỉnh sửa
    readonly_fields = [
        'uploaded_by', 'uploaded_at', 'ocr_start_time', 'ocr_end_time', 
        'match_score', 
        'original_filename',      # SỬA LỖI
        'processing_duration',    # SỬA LỖI
        'status', 'raw_ocr_text'
    ]

    inlines = [ExtractedFieldInline]


# Đăng ký Admin cho các Model còn lại (để hoàn chỉnh)
@admin.register(ExtractedField)
class ExtractedFieldAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'field_name', 'extracted_value', 'is_verified', 'confidence')
    list_filter = ('is_verified',)
    search_fields = ('invoice__invoice_number', 'field_name', 'extracted_value')
    list_editable = ('is_verified',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'tax_id')
    search_fields = ('name', 'tax_id')

# ... (Các lớp admin khác) ...

# Đăng ký các Model khác để tránh lỗi nếu chúng được tham chiếu
admin.site.register(ERPIntegrationConfig)
admin.site.register(MatchingRule)
admin.site.register(TaskAssignment)
admin.site.register(ActivityLog)