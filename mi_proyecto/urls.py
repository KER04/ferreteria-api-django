from django.contrib import admin
from apps.autenticacion.views import *
from apps.renta.views import *
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/autenticacion/', include('apps.autenticacion.urls')),

    path('usuarios/', UsuarioListView.as_view(), name='usuario-list-create'),
    path('usuarios/<int:pk>/', UsuarioRetrieveUpdateDestroyView.as_view(), name='usuario-detail'),
    
    path('api/renta/', include('apps.renta.urls')),
]
