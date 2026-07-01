from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DevolucionViewSet, OperacionViewSet

router = DefaultRouter()
router.register(r"operaciones",  OperacionViewSet,  basename="operacion")
router.register(r"devoluciones", DevolucionViewSet, basename="devolucion")

urlpatterns = [
    path("", include(router.urls)),
]
