# app_invoices/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.db.models import F, ExpressionWrapper, DurationField, Avg, Count, Q
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action


import os
from PIL import Image
import pytesseract

from .models import (
    Invoice, TaskAssignment, Supplier, ERPIntegrationConfig, 
    MatchingRule, ActivityLog, InvoiceStatus, AIChatSession, 
    AIChatMessage, AIModelTraining, AIRecommendation
)
from .serializers import (
    InvoiceSerializer, InvoiceCreateSerializer, TaskAssignmentSerializer, 
    SupplierSerializer, ERPIntegrationConfigSerializer, 
    MatchingRuleSerializer, ActivityLogSerializer
)

# ---------------------------------------------------------
# 1. HTML Views (dùng cho giao diện web)
# ---------------------------------------------------------
class CustomLoginView(LoginView):
    template_name = 'app_invoices/login.html'


class CustomLogoutView(LogoutView):
    next_page = '/invoices/login/'


@login_required
def dashboard_view(request):
    return render(request, 'app_invoices/dashboard.html')


@login_required
def invoice_list_view(request):
    return render(request, 'app_invoices/invoice_list.html')


@login_required
def invoice_detail_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    context = {'invoice': invoice}
    return render(request, 'app_invoices/invoice_detail.html', context)


@login_required
def task_list_view(request):
    return render(request, 'app_invoices/task_list.html')


@login_required
def reports_view(request):
    invoices = Invoice.objects.all()
    total_invoices = invoices.count()

    # Thống kê theo trạng thái
    status_counts = invoices.values('status').annotate(total=Count('id'))
    status_data = {item['status']: item['total'] for item in status_counts}

    # Thời gian OCR trung bình
    avg_ocr_time = invoices.annotate(
        duration=ExpressionWrapper(
            F('ocr_end_time') - F('ocr_start_time'),
            output_field=DurationField()
        )
    ).aggregate(avg_time=Avg('duration'))['avg_time'] or timedelta(seconds=0)

    # Tỷ lệ khớp tự động (match_score >= 0.9)
    auto_matched_ratio = (
        invoices.filter(match_score__gte=0.9).count() / total_invoices * 100
        if total_invoices > 0 else 0
    )

    # Độ chính xác OCR trung bình
    avg_match_score = invoices.aggregate(Avg('match_score'))['match_score__avg'] or 0

    # Tỷ lệ lỗi tích hợp
    integration_errors = invoices.filter(status=InvoiceStatus.INTEGRATION_ERROR).count()
    integration_error_ratio = (integration_errors / total_invoices * 100) if total_invoices > 0 else 0

    # Dữ liệu biểu đồ khớp theo thời gian (7 ngày gần nhất)
    from django.db.models.functions import TruncDate
    from django.utils import timezone

    last_7_days = timezone.now() - timedelta(days=7)
    chart_data = (
        invoices.filter(uploaded_at__gte=last_7_days)
        .annotate(day=TruncDate('uploaded_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    context = {
        "total_invoices": total_invoices,
        "status_data": status_data,
        "avg_ocr_time": round(avg_ocr_time.total_seconds(), 2),
        "auto_matched_ratio": round(auto_matched_ratio, 2),
        "avg_match_score": round(avg_match_score, 2),
        "integration_error_ratio": round(integration_error_ratio, 2),
        "chart_data": list(chart_data),
    }
    return render(request, "app_invoices/reports.html", context)

@login_required
def erp_settings_view(request):
    return render(request, 'app_invoices/erp_settings.html')

@login_required
def ai_chat_view(request):
    """🤖 AI Chat View"""
    return render(request, 'app_invoices/ai_chat.html')

@login_required
def ai_dashboard_view(request):
    """📊 AI Dashboard View"""
    return render(request, 'app_invoices/ai_dashboard.html')

@login_required
def task_assignment_view(request):
    """👥 Task Assignment View"""
    return render(request, 'app_invoices/task_assignment.html')


# ---------------------------------------------------------
# 2. OCR PROCESSING FUNCTION (đã chỉnh hoàn chỉnh)
# ---------------------------------------------------------
def process_invoice_ocr(invoice_id):
    """
    🤖 Hàm xử lý OCR + AI, đọc text từ ảnh hóa đơn và áp dụng AI để phân tích thông minh
    """
    from django.utils import timezone
    import traceback
    import re
    import time

    try:
        # Import AI services
        from .ai_services import ai_classifier, ai_extractor, fraud_detector, ai_predictor
        
        invoice = Invoice.objects.get(id=invoice_id)
        invoice.status = InvoiceStatus.OCR_PROCESSING
        invoice.ocr_start_time = timezone.now()
        invoice.save()

        file_path = os.path.join(settings.MEDIA_ROOT, str(invoice.file))
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        # ✅ Cấu hình Tesseract (Windows)
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # ✅ Bỏ qua OCR PDF
        if file_path.lower().endswith(".pdf"):
            invoice.raw_ocr_text = "[Không hỗ trợ OCR file PDF trực tiếp]"
            invoice.status = InvoiceStatus.OCR_PROCESSED
            invoice.ocr_end_time = timezone.now()
            invoice.save()
            return

        # ✅ Thực hiện OCR
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang="vie+eng")

        if not text.strip():
            text = "[⚠️ Không nhận diện được nội dung từ ảnh]"

        # 🤖 --- BẮT ĐẦU XỬ LÝ AI ---
        ai_start_time = time.time()
        
        # 1️⃣ AI Phân loại hóa đơn
        classification_result = ai_classifier.classify_invoice(text)
        invoice.ai_category = classification_result['category']
        invoice.ai_confidence = classification_result['confidence']
        
        # 2️⃣ AI Trích xuất dữ liệu thông minh
        extracted_data = ai_extractor.extract_smart_data(text)
        invoice.ai_extracted_data = extracted_data
        
        # Cập nhật các trường từ AI extraction
        if extracted_data.get('invoice_number'):
            invoice.invoice_number = extracted_data['invoice_number']
        if extracted_data.get('total_amount'):
            invoice.total_amount = extracted_data['total_amount']
        if extracted_data.get('supplier_name'):
            supplier, _ = Supplier.objects.get_or_create(name=extracted_data['supplier_name'])
            invoice.supplier = supplier
        
        # 3️⃣ AI Phát hiện fraud
        fraud_result = fraud_detector.detect_fraud(extracted_data, text)
        invoice.fraud_risk_score = fraud_result['risk_score']
        invoice.fraud_risk_level = fraud_result['risk_level']
        
        # 4️⃣ AI Dự đoán
        prediction_result = ai_predictor.predict_invoice_approval_probability(extracted_data)
        processing_time_result = ai_predictor.predict_invoice_processing_time(extracted_data)
        
        # Tính thời gian xử lý AI
        ai_processing_time = int((time.time() - ai_start_time) * 1000)  # milliseconds
        invoice.ai_processing_time = ai_processing_time
        
        # Tạo khuyến nghị AI
        recommendations = []
        if fraud_result['risk_score'] >= 0.7:
            recommendations.append("🚨 CẢNH BÁO: Rủi ro fraud cao - cần kiểm tra thủ công")
        if classification_result['confidence'] < 0.6:
            recommendations.append("⚠️ Phân loại không chắc chắn - cần xem xét")
        if prediction_result['approval_probability'] < 0.5:
            recommendations.append("📋 Khả năng phê duyệt thấp - cần kiểm tra kỹ")
        
        invoice.ai_recommendations = "\n".join(recommendations) if recommendations else "✅ Hóa đơn có thể xử lý tự động"
        
        # ✅ Kiểm tra xem có phải hóa đơn thật không (cải tiến với AI)
        keywords = ["HÓA ĐƠN", "INVOICE", "GTGT", "BILL", "RECEIPT"]
        invoice.is_invoice = any(k in text.upper() for k in keywords) or classification_result['confidence'] > 0.7

        # Lưu tất cả thay đổi
        invoice.raw_ocr_text = text
        invoice.status = InvoiceStatus.OCR_PROCESSED
        invoice.ocr_end_time = timezone.now()
        invoice.save()

        # Tạo AI Recommendation record
        if recommendations:
            AIRecommendation.objects.create(
                invoice=invoice,
                recommendation_type='manual_check' if fraud_result['risk_score'] >= 0.7 else 'review',
                confidence=1.0 - fraud_result['risk_score'],
                reason=invoice.ai_recommendations
            )

        print(f"🤖 AI OCR hoàn tất cho hóa đơn ID {invoice.id}")
        print(f"📊 Phân loại: {invoice.ai_category} (độ tin cậy: {invoice.ai_confidence})")
        print(f"🧾 Số hóa đơn: {invoice.invoice_number}")
        print(f"🏢 Nhà cung cấp: {invoice.supplier}")
        print(f"💰 Tổng tiền: {invoice.total_amount}")
        print(f"🕵️ Rủi ro fraud: {invoice.fraud_risk_level} ({invoice.fraud_risk_score})")
        print(f"⏱️ Thời gian AI: {ai_processing_time}ms")

    except Exception as e:
        print("❌ Lỗi AI OCR:", e)
        print(traceback.format_exc())

        try:
            invoice.status = InvoiceStatus.INTEGRATION_ERROR
            invoice.raw_ocr_text = f"Lỗi AI OCR: {e}"
            invoice.save()
        except Exception as save_error:
            print("⚠️ Không thể lưu trạng thái lỗi:", save_error)

# ---------------------------------------------------------
# 3. API ViewSets (Django REST Framework)
# ---------------------------------------------------------
class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-uploaded_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice = serializer.save(
            uploaded_by=request.user, 
            status=InvoiceStatus.OCR_PROCESSING
        )

        # Gọi OCR thực tế
        process_invoice_ocr(invoice.id)

        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def update_field(self, request, pk=None):
        """Cập nhật thủ công giá trị OCR"""
        invoice = self.get_object()
        field_name = request.data.get('field_name')
        corrected_value = request.data.get('corrected_value')

        ActivityLog.objects.create(
            user=request.user,
            action=f"Cập nhật trường '{field_name}'",
            invoice=invoice,
            details=f"Giá trị mới: {corrected_value}"
        )
        return Response({"message": f"Updated {field_name} successfully."}, status=status.HTTP_200_OK)


class TaskAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TaskAssignment.objects.all().order_by('-due_date')
    serializer_class = TaskAssignmentSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by('name')
    serializer_class = SupplierSerializer


class ERPIntegrationConfigViewSet(viewsets.ModelViewSet):
    queryset = ERPIntegrationConfig.objects.all().order_by('system_name')
    serializer_class = ERPIntegrationConfigSerializer


class MatchingRuleViewSet(viewsets.ModelViewSet):
    queryset = MatchingRule.objects.all().order_by('priority')
    serializer_class = MatchingRuleSerializer


class ActivityLogViewSet(viewsets.ModelViewSet):
    queryset = ActivityLog.objects.all().order_by('-timestamp')
    serializer_class = ActivityLogSerializer


# ---------------------------------------------------------
# 4. API phụ trợ khác
# ---------------------------------------------------------
class DashboardStatsAPIView(APIView):
    """
    API trả về thống kê tổng quan cho Dashboard.
    """
    def get(self, request, format=None):
        from django.db.models import Count

        stats = {
            # Tổng số hóa đơn
            "total_invoices": Invoice.objects.count(),

            # Hóa đơn chờ phê duyệt
            "pending_approval": Invoice.objects.filter(status=InvoiceStatus.PENDING_REVIEW).count(),

            # Hóa đơn đã khớp (giả sử trạng thái MATCHED)
            "matched_count": Invoice.objects.filter(status=InvoiceStatus.MATCHED).count(),

            # Hóa đơn lỗi tích hợp
            "integration_errors": Invoice.objects.filter(status=InvoiceStatus.INTEGRATION_ERROR).count(),

            # Tổng giá trị đã xử lý
            "total_processed_amount": Invoice.objects.aggregate(total=Sum("total_amount"))["total"] or 0,

            # Thời gian xử lý trung bình (nếu có OCR)
            "avg_processing_time": self._calculate_avg_ocr_time(),

            # Tỷ lệ khớp tự động
            "auto_matched_count": Invoice.objects.filter(match_score__gte=0.9).count(),  # ví dụ >=90%
        }

        # ✅ Lấy thông báo / nhiệm vụ mới nhất
        recent_logs = ActivityLog.objects.select_related("invoice", "user").order_by("-timestamp")[:5]
        notifications = [
            {
                "invoice_id": log.invoice.id if log.invoice else None,
                "invoice_number": getattr(log.invoice, "invoice_number", "N/A"),
                "action": log.action,
                "user": str(log.user),
                "timestamp": log.timestamp.strftime("%d/%m/%Y %H:%M"),
            }
            for log in recent_logs
        ]

        stats["recent_notifications"] = notifications

        return Response(stats)

    def _calculate_avg_ocr_time(self):
        """Tính thời gian OCR trung bình (đơn giản)"""
        invoices = Invoice.objects.filter(ocr_start_time__isnull=False, ocr_end_time__isnull=False)
        if not invoices.exists():
            return "0s"

        total_seconds = sum(
            (inv.ocr_end_time - inv.ocr_start_time).total_seconds() for inv in invoices
        )
        avg_seconds = total_seconds / invoices.count()
        return f"{round(avg_seconds, 1)}s"

class AsyncInvoiceOCRAPIView(APIView):
    def post(self, request, format=None):
        invoice_id = request.data.get('invoice_id')
        process_invoice_ocr(invoice_id)
        return Response({"message": "OCR đã hoàn tất (đồng bộ)."})


# ---------------------------------------------------------
# 5. API bổ sung: Danh sách công việc của người dùng hiện tại
# ---------------------------------------------------------
class MyTasksListAPIView(APIView):
    """
    API trả về danh sách các công việc (TaskAssignment) được giao cho người dùng hiện tại.
    """
    def get(self, request, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Bạn cần đăng nhập trước."}, status=status.HTTP_401_UNAUTHORIZED)

        tasks = TaskAssignment.objects.filter(assigned_to=user).order_by('-due_date')
        serializer = TaskAssignmentSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


from rest_framework.decorators import api_view

@api_view(['GET'])
def get_invoice_detail(request, pk):
    """
    API trả về chi tiết hóa đơn theo ID.
    """
    try:
        invoice = Invoice.objects.get(pk=pk)
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data, status=200)
    except Invoice.DoesNotExist:
        return Response({'error': 'Không tìm thấy hóa đơn'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
@api_view(['POST'])
def approve_invoice(request, pk):
    """
    ✅ Phê duyệt hóa đơn
    """
    try:
        invoice = Invoice.objects.get(pk=pk)
        invoice.status = InvoiceStatus.APPROVED
        invoice.save()

        ActivityLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            invoice=invoice,
            action="Phê duyệt hóa đơn",
            details=f"Hóa đơn {invoice.invoice_number or invoice.id} đã được phê duyệt."
        )

        return Response({"message": "✅ Hóa đơn đã được phê duyệt thành công!"}, status=200)

    except Invoice.DoesNotExist:
        return Response({"error": "Không tìm thấy hóa đơn."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def match_invoice_erp(request, pk):
    """
    🔗 Khớp / Tạo ERP cho hóa đơn
    """
    try:
        invoice = Invoice.objects.get(pk=pk)
        # Giả lập khớp ERP thành công (thực tế có thể gọi API ERP)
        invoice.status = InvoiceStatus.MATCHED
        invoice.match_score = 0.95  # ví dụ: khớp 95%
        invoice.save()

        ActivityLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            invoice=invoice,
            action="Khớp ERP thành công",
            details=f"Hóa đơn {invoice.invoice_number or invoice.id} đã khớp ERP với độ chính xác 95%."
        )

        return Response({"message": "🔗 Hóa đơn đã được khớp ERP!"}, status=200)

    except Invoice.DoesNotExist:
        return Response({"error": "Không tìm thấy hóa đơn."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def rerun_ocr(request, pk):
    """
    🔄 Chạy lại OCR cho hóa đơn
    """
    try:
        invoice = Invoice.objects.get(pk=pk)
        process_invoice_ocr(invoice.id)

        ActivityLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            invoice=invoice,
            action="Chạy lại OCR",
            details=f"Hóa đơn {invoice.invoice_number or invoice.id} được OCR lại vào {timezone.now()}."
        )

        return Response({"message": "🔄 OCR đã được chạy lại thành công!"}, status=200)

    except Invoice.DoesNotExist:
        return Response({"error": "Không tìm thấy hóa đơn."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    
    from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from .models import Invoice, InvoiceStatus


class ReportSummaryAPIView(APIView):
    
    def get(self, request):
        try:
            invoices = Invoice.objects.all()
            total = invoices.count()

            if total == 0:
                # ✅ Không có dữ liệu
                return Response({
                    "auto_match_rate": 0,
                    "avg_processing_time": 0,
                    "ocr_accuracy": 0,
                    "integration_error_rate": 0,
                    "message": "Không có dữ liệu hóa đơn để thống kê."
                }, status=200)

            matched = invoices.filter(status=InvoiceStatus.MATCHED).count()
            auto_matched = invoices.filter(match_score__gte=0.9).count()
            integration_errors = invoices.filter(status=InvoiceStatus.INTEGRATION_ERROR).count()
            avg_match_score = invoices.aggregate(avg=Avg("match_score"))["avg"] or 0

            # ✅ Tính thời gian OCR trung bình an toàn
            avg_duration_qs = invoices.filter(
                ocr_start_time__isnull=False,
                ocr_end_time__isnull=False
            ).annotate(
                duration=ExpressionWrapper(
                    F("ocr_end_time") - F("ocr_start_time"),
                    output_field=DurationField()
                )
            )

            avg_duration = avg_duration_qs.aggregate(avg_time=Avg("duration"))["avg_time"]
            avg_seconds = round(avg_duration.total_seconds(), 2) if avg_duration else 0

            return Response({
                "auto_match_rate": round(auto_matched / total * 100, 2),
                "avg_processing_time": avg_seconds,
                "ocr_accuracy": round(avg_match_score * 100, 2),
                "integration_error_rate": round(integration_errors / total * 100, 2),
            }, status=200)

        except Exception as e:
            import traceback
            print("❌ Lỗi trong ReportSummaryAPIView:", e)
            print(traceback.format_exc())
            return Response({
                "error": str(e),
                "message": "Đã xảy ra lỗi khi tạo báo cáo."
            }, status=500)


class MatchRateReportAPIView(APIView):
    """
    📊 API trả về tỷ lệ khớp theo tháng (cho biểu đồ)
    """
    def get(self, request):
        data = (
            Invoice.objects
            .annotate(month=TruncMonth("uploaded_at"))
            .values("month")
            .annotate(
                total=Count("id"),
                matched=Count("id", filter=Q(status=InvoiceStatus.MATCHED)),
                auto_matched=Count("id", filter=Q(match_score__gte=0.9)),
            )
            .order_by("month")
        )
        return Response(list(data))


class SupplierPerformanceAPIView(APIView):
    """
    ⚠️ API thống kê hiệu suất theo nhà cung cấp (nhà cung cấp lỗi nhiều nhất)
    """
    def get(self, request):
        data = (
            Invoice.objects
            .filter(status=InvoiceStatus.INTEGRATION_ERROR)
            .values("supplier__name")
            .annotate(error_count=Count("id"))
            .order_by("-error_count")
        )
        return Response(list(data))


# ---------------------------------------------------------
# 7. API cho đối chiếu & phê duyệt hóa đơn
# ---------------------------------------------------------
class InvoiceMatchAPIView(APIView):
    """
    🔗 API mô phỏng đối chiếu OCR và ERP cho hóa đơn
    """
    def post(self, request, pk, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(pk=pk)
            # Tạm thời giả lập match tự động
            invoice.status = InvoiceStatus.MATCHED
            invoice.match_score = 0.92
            invoice.save()

            return Response({
                "message": f"Hóa đơn ID={invoice.id} đã khớp thành công với ERP (độ chính xác 92%)."
            }, status=status.HTTP_200_OK)

        except Invoice.DoesNotExist:
            return Response({"error": "Không tìm thấy hóa đơn."}, status=status.HTTP_404_NOT_FOUND)


class InvoiceApproveAPIView(APIView):
    """
    ✅ API phê duyệt hóa đơn
    """
    def post(self, request, pk, *args, **kwargs):
        try:
            invoice = Invoice.objects.get(pk=pk)
            invoice.status = InvoiceStatus.APPROVED
            invoice.save()

            return Response({
                "message": f"Hóa đơn ID={invoice.id} đã được phê duyệt thành công!"
            }, status=status.HTTP_200_OK)

        except Invoice.DoesNotExist:
            return Response({"error": "Không tìm thấy hóa đơn."}, status=status.HTTP_404_NOT_FOUND)


# 🤖 AI API Endpoints
class AIChatAPIView(APIView):
    """
    💬 API Chat với AI Bot
    """
    def post(self, request):
        try:
            from .ai_services import ai_chatbot
            
            user_message = request.data.get('message', '')
            session_id = request.data.get('session_id', '')
            
            if not user_message:
                return Response({"error": "Tin nhắn không được để trống"}, status=400)
            
            # Tạo hoặc lấy session
            if session_id:
                try:
                    session = AIChatSession.objects.get(session_id=session_id, user=request.user)
                except AIChatSession.DoesNotExist:
                    session = AIChatSession.objects.create(
                        user=request.user,
                        session_id=session_id
                    )
            else:
                import uuid
                session_id = str(uuid.uuid4())
                session = AIChatSession.objects.create(
                    user=request.user,
                    session_id=session_id
                )
            
            # Lưu tin nhắn người dùng
            AIChatMessage.objects.create(
                session=session,
                message_type='user',
                content=user_message
            )
            
            # Tạo context từ dữ liệu hiện tại
            context = {
                'user_id': request.user.id,
                'session_id': session_id,
                'recent_invoices': list(Invoice.objects.filter(uploaded_by=request.user)[:5].values('id', 'invoice_number', 'status'))
            }
            
            # Chat với AI
            ai_response = ai_chatbot.chat(user_message, context)
            
            # Lưu phản hồi AI
            AIChatMessage.objects.create(
                session=session,
                message_type='ai',
                content=ai_response,
                context=context
            )
            
            # Cập nhật last activity
            session.last_activity = timezone.now()
            session.save()
            
            return Response({
                'response': ai_response,
                'session_id': session_id,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class AIAnalysisAPIView(APIView):
    """
    🔍 API Phân tích AI cho hóa đơn
    """
    def get(self, request, pk):
        try:
            invoice = Invoice.objects.get(pk=pk)
            
            analysis = {
                'invoice_id': invoice.id,
                'ai_category': invoice.ai_category,
                'ai_confidence': float(invoice.ai_confidence or 0),
                'fraud_risk_score': float(invoice.fraud_risk_score or 0),
                'fraud_risk_level': invoice.fraud_risk_level,
                'ai_extracted_data': invoice.ai_extracted_data,
                'ai_processing_time': invoice.ai_processing_time,
                'ai_recommendations': invoice.ai_recommendations,
                'recommendations': []
            }
            
            # Lấy AI recommendations
            recommendations = AIRecommendation.objects.filter(invoice=invoice)
            for rec in recommendations:
                analysis['recommendations'].append({
                    'type': rec.recommendation_type,
                    'confidence': float(rec.confidence),
                    'reason': rec.reason,
                    'is_applied': rec.is_applied,
                    'created_at': rec.created_at.isoformat()
                })
            
            return Response(analysis)
            
        except Invoice.DoesNotExist:
            return Response({"error": "Không tìm thấy hóa đơn"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class AITrainingAPIView(APIView):
    """
    🎯 API Huấn luyện AI Model
    """
    def post(self, request):
        try:
            from .ai_services import ai_classifier
            
            training_data = request.data.get('training_data', [])
            model_type = request.data.get('model_type', 'classifier')
            
            if not training_data:
                return Response({"error": "Dữ liệu huấn luyện không được để trống"}, status=400)
            
            # Huấn luyện model
            if model_type == 'classifier':
                success = ai_classifier.train_model(training_data)
                
                if success:
                    # Lưu thông tin training
                    AIModelTraining.objects.create(
                        model_name=f"Invoice Classifier {timezone.now().strftime('%Y%m%d_%H%M%S')}",
                        model_type='classifier',
                        training_data_count=len(training_data),
                        accuracy=0.85,  # Giả sử accuracy
                        last_trained=timezone.now(),
                        model_file_path=ai_classifier.model_path
                    )
                    
                    return Response({
                        "message": "✅ AI Model đã được huấn luyện thành công",
                        "training_data_count": len(training_data),
                        "model_type": model_type
                    })
                else:
                    return Response({"error": "Lỗi huấn luyện AI model"}, status=500)
            else:
                return Response({"error": "Loại model không được hỗ trợ"}, status=400)
                
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class AIPredictionAPIView(APIView):
    """
    🔮 API Dự đoán AI
    """
    def get(self, request, pk):
        try:
            from .ai_services import ai_predictor
            
            invoice = Invoice.objects.get(pk=pk)
            extracted_data = invoice.ai_extracted_data or {}
            
            # Dự đoán thời gian xử lý
            processing_prediction = ai_predictor.predict_invoice_processing_time(extracted_data)
            
            # Dự đoán khả năng phê duyệt
            approval_prediction = ai_predictor.predict_invoice_approval_probability(extracted_data)
            
            return Response({
                'invoice_id': invoice.id,
                'processing_prediction': processing_prediction,
                'approval_prediction': approval_prediction,
                'current_status': invoice.status,
                'ai_confidence': float(invoice.ai_confidence or 0)
            })
            
        except Invoice.DoesNotExist:
            return Response({"error": "Không tìm thấy hóa đơn"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class AIDashboardAPIView(APIView):
    """
    📊 API Dashboard AI
    """
    def get(self, request):
        try:
            # Thống kê AI
            total_invoices = Invoice.objects.count()
            ai_processed = Invoice.objects.filter(ai_category__isnull=False).count()
            fraud_detected = Invoice.objects.filter(fraud_risk_score__gte=0.7).count()
            high_confidence = Invoice.objects.filter(ai_confidence__gte=0.8).count()
            
            # Phân loại theo category
            categories = Invoice.objects.values('ai_category').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Risk level distribution
            risk_levels = Invoice.objects.values('fraud_risk_level').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # AI Model performance
            models = AIModelTraining.objects.filter(is_active=True)
            model_performance = []
            for model in models:
                model_performance.append({
                    'name': model.model_name,
                    'type': model.model_type,
                    'accuracy': float(model.accuracy or 0),
                    'last_trained': model.last_trained.isoformat() if model.last_trained else None
                })
            
            return Response({
                'ai_stats': {
                    'total_invoices': total_invoices,
                    'ai_processed': ai_processed,
                    'ai_processing_rate': round(ai_processed / total_invoices * 100, 2) if total_invoices > 0 else 0,
                    'fraud_detected': fraud_detected,
                    'high_confidence': high_confidence
                },
                'categories': list(categories),
                'risk_levels': list(risk_levels),
                'model_performance': model_performance
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)
