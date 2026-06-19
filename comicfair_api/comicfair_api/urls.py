from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/exhibitions/', include('exhibitions.urls')),
    path('api/booths/', include('booths.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/tickets/', include('tickets.urls')),
    path('api/checkins/', include('checkins.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
