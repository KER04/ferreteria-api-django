from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenRefreshView

from apps.autenticacion.views import UsuarioListView, UsuarioRetrieveUpdateDestroyView

from .health import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health check para monitoreo / orquestadores
    path('health/', HealthCheckView.as_view(), name='health'),

    # Documentación de la API (OpenAPI / Swagger / Redoc)
    path('api/schema/',      SpectacularAPIView.as_view(),                          name='schema'),
    path('api/docs/',        SpectacularSwaggerView.as_view(url_name='schema'),     name='swagger-ui'),
    path('api/redoc/',       SpectacularRedocView.as_view(url_name='schema'),       name='redoc'),

    # Autenticación (login, logout, registro, roles, recursos)
    path('api/auth/', include('apps.autenticacion.urls')),

    # Refresh token JWT
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Usuarios (CRUD protegido con IsAdminRole)
    path('usuarios/',             UsuarioListView.as_view(),                   name='usuario-list'),
    path('usuarios/<int:pk>/',    UsuarioRetrieveUpdateDestroyView.as_view(),  name='usuario-detail'),

    # Inventario (productos, marcas, categorías, préstamos)
    path('api/inventario/', include('apps.inventario.urls')),

    # Operaciones (ventas, préstamos, devoluciones)
    path('api/operaciones/', include('apps.operaciones.urls')),

    # Mantenimiento (costos, tipos, registros, salidas)
    path('api/mantenimiento/', include('apps.mantenimiento.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
