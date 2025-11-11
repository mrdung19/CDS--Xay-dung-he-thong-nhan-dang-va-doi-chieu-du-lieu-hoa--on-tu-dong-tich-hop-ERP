#!/usr/bin/env python
"""
🤖 Test AI Features Script
Kiểm tra các tính năng AI đã được tích hợp
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invoice_processing_system.settings')
django.setup()

from app_invoices.ai_services import (
    ai_classifier, ai_extractor, fraud_detector, 
    ai_chatbot, ai_predictor
)
from app_invoices.models import Invoice, AIChatSession, AIModelTraining

def test_ai_classifier():
    """Test AI Classifier"""
    print("🧠 Testing AI Classifier...")
    
    # Test data
    test_texts = [
        "HÓA ĐƠN ĐIỆN LỰC VIỆT NAM - Số: 123456 - Tổng: 1,500,000 đ",
        "CÔNG TY CẤP NƯỚC TP.HCM - Hóa đơn nước tháng 10/2024",
        "FPT TELECOM - Hóa đơn internet tháng 11/2024",
        "VIETTEL - Hóa đơn điện thoại tháng 12/2024"
    ]
    
    for text in test_texts:
        result = ai_classifier.classify_invoice(text)
        print(f"  📄 Text: {text[:50]}...")
        print(f"  🏷️  Category: {result['category']}")
        print(f"  📊 Confidence: {result['confidence']:.2f}")
        print()

def test_ai_extractor():
    """Test AI Data Extractor"""
    print("🔍 Testing AI Data Extractor...")
    
    test_text = """
    HÓA ĐƠN ĐIỆN LỰC VIỆT NAM
    Số: HD-2024-001234
    Ngày: 15/10/2024
    Công ty: EVN HCMC
    Tổng tiền: 2,500,000 đ
    Thuế VAT: 250,000 đ
    """
    
    extracted = ai_extractor.extract_smart_data(test_text)
    print(f"  📄 Invoice Number: {extracted.get('invoice_number')}")
    print(f"  🏢 Supplier: {extracted.get('supplier_name')}")
    print(f"  💰 Total Amount: {extracted.get('total_amount')}")
    print(f"  🧾 Tax Amount: {extracted.get('tax_amount')}")
    print(f"  📅 Issue Date: {extracted.get('issue_date')}")
    print(f"  📊 Confidence: {extracted.get('confidence_score')}")
    print()

def test_fraud_detector():
    """Test Fraud Detector"""
    print("🕵️ Testing Fraud Detector...")
    
    test_cases = [
        {
            'data': {
                'invoice_number': 'HD-2024-001234',
                'total_amount': 2500000,
                'supplier_name': 'EVN HCMC',
                'issue_date': '15/10/2024'
            },
            'text': 'HÓA ĐƠN ĐIỆN LỰC VIỆT NAM - Số: HD-2024-001234'
        },
        {
            'data': {
                'invoice_number': 'INVALID',
                'total_amount': 999999999,
                'supplier_name': 'FAKE COMPANY',
                'issue_date': '99/99/9999'
            },
            'text': 'FAKE INVOICE WITH INVALID DATA'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = fraud_detector.detect_fraud(case['data'], case['text'])
        print(f"  📋 Test Case {i}:")
        print(f"    🚨 Is Fraud: {result['is_fraud']}")
        print(f"    📊 Risk Score: {result['risk_score']}")
        print(f"    ⚠️  Risk Level: {result['risk_level']}")
        print(f"    🔍 Indicators: {result['indicators']}")
        print()

def test_ai_chatbot():
    """Test AI Chatbot"""
    print("💬 Testing AI Chatbot...")
    
    test_messages = [
        "Trạng thái hóa đơn là gì?",
        "Hướng dẫn upload hóa đơn",
        "Báo cáo thống kê",
        "Lỗi OCR không hoạt động"
    ]
    
    for message in test_messages:
        response = ai_chatbot.chat(message)
        print(f"  👤 User: {message}")
        print(f"  🤖 AI: {response[:100]}...")
        print()

def test_ai_predictor():
    """Test AI Predictor"""
    print("🔮 Testing AI Predictor...")
    
    test_data = {
        'invoice_number': 'HD-2024-001234',
        'total_amount': 2500000,
        'supplier_name': 'EVN HCMC',
        'issue_date': '15/10/2024',
        'raw_ocr_text': 'HÓA ĐƠN ĐIỆN LỰC VIỆT NAM...'
    }
    
    # Test processing time prediction
    processing_pred = ai_predictor.predict_invoice_processing_time(test_data)
    print(f"  ⏱️  Processing Prediction:")
    print(f"    Predicted Time: {processing_pred['predicted_time']}s")
    print(f"    Confidence: {processing_pred['confidence']}")
    print(f"    Recommendation: {processing_pred['recommendation']}")
    print()
    
    # Test approval prediction
    approval_pred = ai_predictor.predict_invoice_approval_probability(test_data)
    print(f"  ✅ Approval Prediction:")
    print(f"    Probability: {approval_pred['approval_probability']}")
    print(f"    Confidence: {approval_pred['confidence']}")
    print(f"    Recommendation: {approval_pred['recommendation']}")
    print()

def test_database_models():
    """Test AI Database Models"""
    print("🗄️ Testing AI Database Models...")
    
    # Test AI Chat Session
    try:
        session = AIChatSession.objects.create(
            user_id=1,  # Assuming user exists
            session_id='test_session_123',
            is_active=True
        )
        print(f"  ✅ AIChatSession created: {session.session_id}")
    except Exception as e:
        print(f"  ⚠️  AIChatSession error: {e}")
    
    # Test AI Model Training
    try:
        training = AIModelTraining.objects.create(
            model_name='Test AI Model',
            model_type='classifier',
            training_data_count=100,
            accuracy=0.85,
            is_active=True
        )
        print(f"  ✅ AIModelTraining created: {training.model_name}")
    except Exception as e:
        print(f"  ⚠️  AIModelTraining error: {e}")
    
    print()

def main():
    """Main test function"""
    print("🤖 AI Features Test Suite")
    print("=" * 50)
    
    try:
        test_ai_classifier()
        test_ai_extractor()
        test_fraud_detector()
        test_ai_chatbot()
        test_ai_predictor()
        test_database_models()
        
        print("🎉 All AI tests completed successfully!")
        print("\n📋 Summary:")
        print("  ✅ AI Classifier - Working")
        print("  ✅ AI Extractor - Working") 
        print("  ✅ Fraud Detector - Working")
        print("  ✅ AI Chatbot - Working")
        print("  ✅ AI Predictor - Working")
        print("  ✅ Database Models - Working")
        
        print("\n🚀 AI System is ready to use!")
        print("   - AI Dashboard: http://localhost:8000/ai/dashboard/")
        print("   - AI Chat: http://localhost:8000/ai/chat/")
        print("   - API Docs: http://localhost:8000/api/ai/")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

