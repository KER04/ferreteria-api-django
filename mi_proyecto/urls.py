from django.contrib import admin
from apps.autenticacion.views import *
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns = [
    path('admin/', admin.site.urls),
 
    # Autenticación (login, logout, registro, roles, recursos)
    path('api/autenticacion/', include('apps.autenticacion.urls')),
 
    # Usuarios (CRUD protegido con IsAdminRole)
    path('usuarios/',        UsuarioListView.as_view(),                name='usuario-list'),
    path('usuarios/<int:pk>/', UsuarioRetrieveUpdateDestroyView.as_view(), name='usuario-detail'),
 
    # Inventario (productos, marcas, categorías, préstamos)
    path('api/inventario/', include('apps.inventario.urls')),
 
    # Renta (rentas, pagos, estados, tipos de pago)
    path('api/operaciones/', include('apps.operaciones.urls')),
    
    # Mantenimiento (costos, tipos, registros, salidas)
    path('api/mantenimiento/', include('apps.mantenimiento.urls')),
]
