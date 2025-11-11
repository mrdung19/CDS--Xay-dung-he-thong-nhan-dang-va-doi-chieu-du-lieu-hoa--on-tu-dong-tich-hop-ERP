from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_invoices(request):
    """Chuyển hướng trang gốc (/) đến Dashboard của ứng dụng."""
    return redirect('/invoices/')

urlpatterns = [
    # 1. URL GỐC
    path('', redirect_to_invoices, name='root-redirect'),
    
    # 2. ADMIN
    path('admin/', admin.site.urls),

    # 3. HTML VIEWS
    path(
        'invoices/',
        include(('invoice_processing_system.app_invoices.urls_html', 'app_invoices'), namespace='app_invoices')
    ),

    # 4. API VIEWS
    path(
        'api/',
        include(('invoice_processing_system.app_invoices.urls_api', 'app_api'), namespace='app_api')
    ),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
