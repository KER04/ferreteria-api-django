from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CostoViewSet,
    MantenimientoViewSet,
    SalidaMantenimientoViewSet,
    TipoMantenimientoViewSet,
)

router = DefaultRouter()
router.register(r"costos",        CostoViewSet,               basename="costo")
router.register(r"tipos",         TipoMantenimientoViewSet,   basename="tipo-mantenimiento")
router.register(r"registros",     MantenimientoViewSet,       basename="mantenimiento")
router.register(r"salidas",       SalidaMantenimientoViewSet, basename="salida-mantenimiento")

urlpatterns = [
    path("", include(router.urls)),
]
