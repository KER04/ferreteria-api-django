# app/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView


from .models import Renta, TipoPago, Estado, Pago, RentaProducto

# Serializers (paquete raíz "serializer")
from serializer.serializers import (
    RentaSerializer,
    TipoPagoSerializer,
    EstadoSerializer,
    PagoSerializer,
    RentaProductoSerializer,
    RentaReadSerializer,
    PagoReadSerializer,
    RentaProductoReadSerializer,
)

# =========================
# RENTA
# =========================
class RentaViewSet(viewsets.ModelViewSet):
    queryset = (
        Renta.objects.select_related("usuario")
        .all()
        .order_by("-renta_fecha_prestamo", "-rent_id")
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["usuario__username"]
    ordering_fields = ["renta_fecha_prestamo", "renta_fecha_devolucion", "rent_id"]

    def get_serializer_class(self):
        return RentaReadSerializer if self.action in ["list", "retrieve"] else RentaSerializer

    # --- CRUD explícito ---
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = self.get_serializer(instance)
        return Response(ser.data)

    def create(self, request, *args, **kwargs):
        ser = RentaSerializer(data=request.data)  # escritura
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        # devolver en formato de lectura
        out = RentaReadSerializer(instance)
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = RentaSerializer(instance, data=request.data)  # escritura
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = RentaReadSerializer(instance)
        return Response(out.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = RentaSerializer(instance, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = RentaReadSerializer(instance)
        return Response(out.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- acciones relacionadas ---
    @action(detail=True, methods=["get"])
    def pagos(self, request, pk=None):
        renta = self.get_object()
        qs = renta.pagos.select_related("tipo_pago", "estado", "renta").all()
        ser = PagoReadSerializer(qs, many=True)
        return Response(ser.data)

    @action(detail=True, methods=["get"])
    def productos(self, request, pk=None):
        renta = self.get_object()
        qs = renta.renta_productos.select_related(
            "producto", "tipo_categoria", "marca", "prestamo", "renta"
        ).all()
        ser = RentaProductoReadSerializer(qs, many=True)
        return Response(ser.data)


# =========================
# TIPO DE PAGO
# =========================
class TipoPagoViewSet(viewsets.ModelViewSet):
    queryset = TipoPago.objects.all().order_by("tipa_nombre", "tipa_id")
    serializer_class = TipoPagoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["tipa_nombre"]
    ordering_fields = ["tipa_nombre", "tipa_id"]

    # CRUD explícito (opcional, mismo patrón)
    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        ser = self.get_serializer(self.get_object())
        return Response(ser.data)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        ser = self.get_serializer(self.get_object(), data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def partial_update(self, request, *args, **kwargs):
        ser = self.get_serializer(self.get_object(), data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================
# ESTADO
# =========================
class EstadoViewSet(viewsets.ModelViewSet):
    queryset = Estado.objects.all().order_by("esta_nombre", "esta_id")
    serializer_class = EstadoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["esta_nombre"]
    ordering_fields = ["esta_nombre", "esta_id"]

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        ser = self.get_serializer(self.get_object(), data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def partial_update(self, request, *args, **kwargs):
        ser = self.get_serializer(self.get_object(), data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================
# PAGO
# =========================
class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.select_related(
        "tipo_pago", "estado", "renta", "renta__usuario"
    ).all().order_by("-pago_fecha_facturacion", "-pago_id")
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "renta__usuario__username",
        "tipo_pago__tipa_nombre",
        "estado__esta_nombre",
    ]
    ordering_fields = ["pago_fecha_facturacion", "pago_total", "pago_id"]

    def get_serializer_class(self):
        return PagoReadSerializer if self.action in ["list", "retrieve"] else PagoSerializer

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        ser = PagoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = PagoReadSerializer(instance)
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = PagoSerializer(instance, data=request.data)
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = PagoReadSerializer(instance)
        return Response(out.data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = PagoSerializer(instance, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = PagoReadSerializer(instance)
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================
# RENTA - PRODUCTO
# =========================
class RentaProductoViewSet(viewsets.ModelViewSet):
    queryset = RentaProducto.objects.select_related(
        "renta", "producto", "tipo_categoria", "marca", "prestamo"
    ).all().order_by("-renta__rent_id")
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "renta__usuario__username",
        "producto__prod_nombre",
        "tipo_categoria__tipr_nombre",
        "marca__marca_nombre",
    ]
    ordering_fields = ["renta__rent_id", "producto__id"]

    def get_serializer_class(self):
        return (
            RentaProductoReadSerializer
            if self.action in ["list", "retrieve"]
            else RentaProductoSerializer
        )

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        ser = RentaProductoSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = RentaProductoReadSerializer(instance)
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = RentaProductoSerializer(instance, data=request.data)
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = RentaProductoReadSerializer(instance)
        return Response(out.data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = RentaProductoSerializer(instance, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = RentaProductoReadSerializer(instance)
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
