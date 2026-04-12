# apps/renta/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RentaViewSet,
    TipoPagoViewSet,
    EstadoViewSet,
    PagoViewSet,
    RentaProductoViewSet,
)

# 🔹 Creamos el router principal
router = DefaultRouter()

# 🔹 Registramos cada recurso
router.register(r'rentas', RentaViewSet, basename='renta')
router.register(r'tipos-pago', TipoPagoViewSet, basename='tipopago')
router.register(r'estados', EstadoViewSet, basename='estado')
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'renta-productos', RentaProductoViewSet, basename='rentaproducto')

# 🔹 Exportamos las rutas
urlpatterns = [
    path('', include(router.urls)),
]
