 

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    #custom admin dashboard (Topic 19)
    path('admin/', admin.site.urls),

    # 2. Interactive Swagger & OpenAPI 3.0 Documentation (Topic 41)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # 3. Authentication & Account Management (Topics 21, 37)
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.products.urls')),
]
