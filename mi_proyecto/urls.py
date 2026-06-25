from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from apps.autenticacion.views import UsuarioListView, UsuarioRetrieveUpdateDestroyView

urlpatterns = [
    path('admin/', admin.site.urls),

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
