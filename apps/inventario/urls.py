from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TipoCategoriaViewSet, MarcaViewSet, PrestamoViewSet, ProductoViewSet

router = DefaultRouter()
router.register(r'tipo-categoria', TipoCategoriaViewSet, basename='tipo-categoria')
router.register(r'marcas', MarcaViewSet, basename='marca')
router.register(r'prestamos', PrestamoViewSet, basename='prestamo')
router.register(r'productos', ProductoViewSet, basename='producto')

urlpatterns = [
    path('', include(router.urls)),
]