from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerSplitView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('allauth.urls')),
    path('api/auth/', include('accounts.urls')),
    path('api/listings/', include('listings.urls')),
    path('api/deals/', include('deals.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/', include('admin_panel.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerSplitView.as_view(url_name='schema'), name='swagger-ui'),
    path('health/', lambda request: JsonResponse({'status': 'ok'})),
]