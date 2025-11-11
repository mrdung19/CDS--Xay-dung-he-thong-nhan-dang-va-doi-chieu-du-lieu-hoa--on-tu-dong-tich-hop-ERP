from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views_api


urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ API app riêng (có namespace)
    path('api/', include(('app_api.urls', 'app_api'), namespace='app_api')),

    # ✅ App giao diện hóa đơn (HTML)
    path('invoices/', include(('app_invoices.urls_html', 'app_invoices'), namespace='app_invoices')),

    # ✅ API của app_invoices (DRF endpoints)
    path('api/', include('app_invoices.urls_api')),
    path('reports/summary/', views_api.report_summary, name='report_summary'),
    path('reports/match-rate/', views_api.match_rate_over_time, name='match_rate'),
    path('reports/supplier-performance/', views_api.supplier_performance, name='supplier_performance'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
