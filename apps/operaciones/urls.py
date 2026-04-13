from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OperacionViewSet, DevolucionViewSet
 
router = DefaultRouter()
router.register(r"operaciones",  OperacionViewSet,  basename="operacion")
router.register(r"devoluciones", DevolucionViewSet, basename="devolucion")
 
urlpatterns = [
    path("", include(router.urls)),
]