# app_invoices/serializers.py
from rest_framework import serializers
from .models import (
    Invoice, ExtractedField, Supplier, TaskAssignment, ERPIntegrationConfig, 
    MatchingRule, ActivityLog
)


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'tax_id']
        
class ExtractedFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedField
        fields = '__all__'

class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Sử dụng cho API POST (tải lên file)"""
    file = serializers.FileField() 

    class Meta:
        model = Invoice
        fields = ('file',)
        
class InvoiceSerializer(serializers.ModelSerializer):
    """Sử dụng cho API GET, PUT, PATCH"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    uploaded_by = serializers.StringRelatedField()
    extracted_fields = ExtractedFieldSerializer(many=True, read_only=True)
    supplier = SupplierSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'file',
            'invoice_number',
            'supplier',
            'status',
            'status_display',
            'total_amount',
            'uploaded_at',
            'uploaded_by',
            'raw_ocr_text',
            'ocr_start_time',
            'ocr_end_time',
            'match_score',
            'extracted_fields',
        ]

    class Meta:
        model = Invoice
        # Bao gồm tất cả các trường mà API cần hiển thị/sửa
        fields = [
            'id', 'file', 'invoice_number', 'supplier', 'status', 'status_display',
            'total_amount', 'uploaded_at', 'uploaded_by', 'raw_ocr_text', 
            'ocr_start_time', 'ocr_end_time', 'match_score', 'extracted_fields'
        ]

class TaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields = '__all__'


        
class ERPIntegrationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ERPIntegrationConfig
        fields = '__all__'

class MatchingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingRule
        fields = '__all__'

class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = '__all__'