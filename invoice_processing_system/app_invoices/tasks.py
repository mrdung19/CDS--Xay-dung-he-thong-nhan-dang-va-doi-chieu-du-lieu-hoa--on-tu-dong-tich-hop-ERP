# app_invoices/tasks.py

from celery import shared_task
from django.utils import timezone
from django.db import transaction
import os
from .models import Invoice, InvoiceStatus, ActivityLog
from .utils import extract_invoice_data


@shared_task(bind=True, max_retries=3)
def process_invoice_ocr(self, invoice_id):
    """Task xử lý OCR cho hóa đơn, có retry và logging."""
    try:
        # 1️⃣ Lấy hóa đơn từ DB (có kiểm tra tồn tại)
        invoice = Invoice.objects.filter(id=invoice_id).first()
        if not invoice:
            print(f"[OCR] ❌ Không tìm thấy Invoice ID={invoice_id}")
            return {"status": "error", "message": f"Invoice {invoice_id} not found"}

        # 2️⃣ Cập nhật trạng thái bắt đầu OCR
        invoice.status = InvoiceStatus.PROCESSING
        invoice.ocr_start_time = timezone.now()
        invoice.original_filename = os.path.basename(invoice.file.name or "")
        invoice.save(update_fields=['status', 'ocr_start_time', 'original_filename'])

        # Ghi nhật ký hoạt động
        ActivityLog.objects.create(
            invoice=invoice,
            action="OCR_STARTED",
            details={"filename": invoice.original_filename}
        )

        # 3️⃣ Thực hiện OCR & trích xuất dữ liệu
        extracted_data = extract_invoice_data(invoice.file.path)

        # 4️⃣ Cập nhật dữ liệu vào DB trong transaction
        with transaction.atomic():
            invoice.invoice_number = extracted_data.get('number')
            invoice.issue_date = extracted_data.get('date')
            invoice.total_amount = extracted_data.get('total')
            invoice.tax_amount = extracted_data.get('tax')
            invoice.raw_ocr_text = extracted_data.get('raw_text')

            # ✅ Nếu OCR thành công
            if invoice.invoice_number and invoice.total_amount:
                invoice.status = InvoiceStatus.OCR_PROCESSED
                ActivityLog.objects.create(
                    invoice=invoice,
                    action="OCR_COMPLETED",
                    details={
                        "number": invoice.invoice_number,
                        "total": str(invoice.total_amount)
                    }
                )
                result_msg = f"OCR success for {invoice.invoice_number}"

            # ❌ Nếu thiếu dữ liệu chính
            else:
                invoice.status = InvoiceStatus.REJECTED
                ActivityLog.objects.create(
                    invoice=invoice,
                    action="OCR_FAILED",
                    details={"error": "Missing key fields after parsing."}
                )
                result_msg = "Missing key fields after OCR"

            invoice.ocr_end_time = timezone.now()
            invoice.save()

        print(f"[OCR] ✅ Hoàn tất: {result_msg}")
        return {"status": "success", "message": result_msg}

    except Exception as exc:
        # 5️⃣ Xử lý lỗi chung và retry nếu có thể
        if 'invoice' in locals() and invoice:
            invoice.status = InvoiceStatus.INTEGRATION_ERROR
            invoice.ocr_end_time = timezone.now()
            invoice.save(update_fields=['status', 'ocr_end_time'])
            ActivityLog.objects.create(
                invoice=invoice,
                action="SYSTEM_ERROR",
                details={"error": str(exc), "attempt": self.request.retries + 1}
            )

        # Cho phép retry nếu lỗi là tạm thời
        raise self.retry(exc=exc, countdown=60)
