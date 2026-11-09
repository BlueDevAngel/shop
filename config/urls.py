from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from decouple import config

admin.site.site_header = "پنل مدیریت فروشگاه"
admin.site.site_title = "مدیریت فروشگاه"
admin.site.index_title = "خوش آمدید - از این بخش کل سایت را مدیریت کنید"

urlpatterns = [
    path(config('ADMIN_URL', default='admin/'), admin.site.urls),
    path('', include('catalog.urls', namespace='catalog')),
    path('', include('core.urls', namespace='core')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('payments/', include('payments.urls', namespace='payments')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)