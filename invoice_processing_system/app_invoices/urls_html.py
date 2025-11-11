# app_invoices/urls_html.py

from django.urls import path
from . import views
from .views import CustomLoginView, CustomLogoutView

app_name = 'app_invoices'
urlpatterns = [
    # Auth Views
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    
    # Main App Views
    # FIX LỖI: Thay đổi 'app-root' thành 'dashboard' để khớp với template HTML
    path('', views.dashboard_view, name='dashboard'), 
    path('invoices/', views.invoice_list_view, name='invoice-list'),
    path('invoices/<int:pk>/detail/', views.invoice_detail_view, name='invoice-detail'),
    path('tasks/', views.task_list_view, name='task-list'),
    path('tasks/assignment/', views.task_assignment_view, name='task-assignment'),
    path('reports/', views.reports_view, name='reports'),
    path('erp-settings/', views.erp_settings_view, name='erp-settings'),
    
    # 🤖 AI Views
    path('ai/chat/', views.ai_chat_view, name='ai-chat'),
    path('ai/dashboard/', views.ai_dashboard_view, name='ai-dashboard'),
]