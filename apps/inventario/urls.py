from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DashboardView,
    MarcaViewSet,
    PrestamoViewSet,
    ProductoViewSet,
    TipoCategoriaViewSet,
)

router = DefaultRouter()
router.register(r'tipo-categoria', TipoCategoriaViewSet, basename='tipo-categoria')
router.register(r'marcas', MarcaViewSet, basename='marca')
router.register(r'prestamos', PrestamoViewSet, basename='prestamo')
router.register(r'productos', ProductoViewSet, basename='producto')

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('', include(router.urls)),
]
