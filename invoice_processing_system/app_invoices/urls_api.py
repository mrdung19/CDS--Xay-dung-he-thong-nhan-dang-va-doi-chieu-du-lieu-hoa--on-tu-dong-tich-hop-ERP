# app_invoices/urls_api.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Import specific views
from .views import (
    ReportSummaryAPIView,
    MatchRateReportAPIView,
    SupplierPerformanceAPIView,
    InvoiceMatchAPIView,
    InvoiceApproveAPIView,
    # AI Views
    AIChatAPIView,
    AIAnalysisAPIView,
    AITrainingAPIView,
    AIPredictionAPIView,
    AIDashboardAPIView,
)

# Khởi tạo Router
router = DefaultRouter()

# ĐĂNG KÝ VIEWSET: Đảm bảo tên lớp (views.InvoiceViewSet, etc.) là chính xác
router.register(r'invoices', views.InvoiceViewSet, basename='api-invoices') 
router.register(r'tasks', views.TaskAssignmentViewSet, basename='api-tasks')
router.register(r'suppliers', views.SupplierViewSet, basename='api-suppliers')
router.register(r'matching-rules', views.MatchingRuleViewSet, basename='api-matching-rules')
router.register(r'activity-logs', views.ActivityLogViewSet, basename='api-activity-logs')
router.register(r'erp-configs', views.ERPIntegrationConfigViewSet, basename='api-erp-configs')

# Định nghĩa URL cho API
app_name = 'app_api'
urlpatterns = [
    # Router URLs (ViewSets)
    path('', include(router.urls)),
    
    # Core API Views
    path('stats/', views.DashboardStatsAPIView.as_view(), name='api-stats'),
    path('dashboard-stats/', views.DashboardStatsAPIView.as_view(), name='api-dashboard-stats'),
    path('my-tasks/', views.MyTasksListAPIView.as_view(), name='api-my-tasks'),
    
    # Invoice Actions
    path('invoices/<int:pk>/approve/', views.approve_invoice, name='api-invoice-approve'),
    path('invoices/<int:pk>/match_erp/', views.match_invoice_erp, name='api-invoice-match-erp'),
    path('invoices/<int:pk>/rerun_ocr/', views.rerun_ocr, name='api-invoice-rerun-ocr'),
    path('invoices/<int:pk>/match/', InvoiceMatchAPIView.as_view(), name='api-invoice-match'),
    
    # OCR Processing
    path('ocr-sync/', views.AsyncInvoiceOCRAPIView.as_view(), name='api-ocr-sync'),
    path('ocr-async/', views.AsyncInvoiceOCRAPIView.as_view(), name='api-ocr-async'),
    
    # Reports
    path('reports/summary/', ReportSummaryAPIView.as_view(), name='api-reports-summary'),
    path('reports/match-rate/', MatchRateReportAPIView.as_view(), name='api-reports-match-rate'),
    path('reports/supplier-performance/', SupplierPerformanceAPIView.as_view(), name='api-reports-supplier-performance'),
    
    # 🤖 AI API Endpoints
    path('ai/chat/', AIChatAPIView.as_view(), name='api-ai-chat'),
    path('ai/analysis/<int:pk>/', AIAnalysisAPIView.as_view(), name='api-ai-analysis'),
    path('ai/training/', AITrainingAPIView.as_view(), name='api-ai-training'),
    path('ai/prediction/<int:pk>/', AIPredictionAPIView.as_view(), name='api-ai-prediction'),
    path('ai/dashboard/', AIDashboardAPIView.as_view(), name='api-ai-dashboard'),
]
