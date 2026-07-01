from decimal import Decimal
from django.db.models import F, Sum, Count, DecimalField
from django.db.models.functions import Coalesce
from rest_framework import viewsets, status, filters, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, inline_serializer

from apps.autenticacion.permissions import IsAdminOrReadOnly

from .models import TipoCategoria, Marca, Prestamo, Producto
from .serializers import (
    TipoCategoriaSerializer,
    MarcaSerializer,
    PrestamoSerializer,
    ProductoSerializer,
    ProductoReadSerializer,
)


# ─────────────────────────────────────────────────────────────────
# Mixin CRUD explícito reutilizable (patrón idéntico al de renta)
# ─────────────────────────────────────────────────────────────────
class ExplicitCRUDMixin:
    def list(self, request, *args, **kwargs):
        qs   = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser  = self.get_serializer(page or qs, many=True)
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


# ─────────────────────────────────────────────────────────────────
# TIPO CATEGORÍA
# ─────────────────────────────────────────────────────────────────
class TipoCategoriaViewSet(ExplicitCRUDMixin, viewsets.ModelViewSet):
    queryset           = TipoCategoria.objects.all().order_by("tipr_nombre")
    serializer_class   = TipoCategoriaSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ["tipr_nombre"]
    ordering_fields    = ["tipr_nombre", "tipr_id"]


# ─────────────────────────────────────────────────────────────────
# MARCA
# ─────────────────────────────────────────────────────────────────
class MarcaViewSet(ExplicitCRUDMixin, viewsets.ModelViewSet):
    queryset           = Marca.objects.all().order_by("marca_nombre")
    serializer_class   = MarcaSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ["marca_nombre"]
    ordering_fields    = ["marca_nombre", "marca_id"]


# ─────────────────────────────────────────────────────────────────
# PRÉSTAMO
# ─────────────────────────────────────────────────────────────────
class PrestamoViewSet(ExplicitCRUDMixin, viewsets.ModelViewSet):
    queryset           = Prestamo.objects.all().order_by("pres_nombre")
    serializer_class   = PrestamoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ["pres_nombre", "tipo_prestamo"]
    ordering_fields    = ["pres_nombre", "pres_id"]


# ─────────────────────────────────────────────────────────────────
# PRODUCTO
# ─────────────────────────────────────────────────────────────────
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = (
        Producto.objects
        .select_related("tipo_categoria", "marca", "prestamo")
        .all()
        .order_by("prod_nombre", "prod_id")
    )
    permission_classes = [IsAdminOrReadOnly]

    # MultiPartParser → botón de upload de imagen en Browsable API
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ["prod_nombre", "codigo_producto"]
    ordering_fields = ["prod_nombre", "prod_valor_unitario", "prod_cantidad_total"]

    def get_queryset(self):
        """
        Filtros opcionales por query param:
          ?marca=1
          ?tipo_categoria=2
          ?prod_estado=Disponible
          ?bajo_stock=true   (disponible <= stock mínimo)
        Sin django-filter para no añadir dependencias.
        """
        qs = super().get_queryset()
        p  = self.request.query_params

        if marca := p.get("marca"):
            qs = qs.filter(marca__marca_id=marca)
        if categoria := p.get("tipo_categoria"):
            qs = qs.filter(tipo_categoria__tipr_id=categoria)
        if estado := p.get("prod_estado"):
            qs = qs.filter(prod_estado=estado)
        if p.get("bajo_stock", "").lower() in ("true", "1", "si", "sí"):
            qs = qs.filter(prod_cantidad_disponible__lte=F("prod_stock_minimo"))

        return qs

    def get_serializer_class(self):
        return ProductoReadSerializer if self.action in ["list", "retrieve"] else ProductoSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    # ── CRUD (escritura → responde con lectura expandida) ────────
    def list(self, request, *args, **kwargs):
        qs   = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser  = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        ser = ProductoSerializer(data=request.data, context=self.get_serializer_context())
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        return Response(
            ProductoReadSerializer(instance, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = ProductoSerializer(instance, data=request.data, context=self.get_serializer_context())
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        return Response(ProductoReadSerializer(instance, context=self.get_serializer_context()).data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = ProductoSerializer(
            instance, data=request.data, partial=True,
            context=self.get_serializer_context(),
        )
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        return Response(ProductoReadSerializer(instance, context=self.get_serializer_context()).data)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────────────────────────
# DASHBOARD / ESTADÍSTICAS
# ─────────────────────────────────────────────────────────────────
@extend_schema(
    responses=inline_serializer("DashboardResponse", {
        "inventario":  serializers.DictField(),
        "operaciones": serializers.DictField(),
    }),
    summary="Resumen del panel de control",
)
class DashboardView(APIView):
    """
    Resumen para el panel de control.
    GET /api/inventario/dashboard/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.operaciones.models import Operacion

        productos = Producto.objects.all()

        valor_inventario = productos.aggregate(
            total=Coalesce(
                Sum(
                    F("prod_cantidad_disponible") * F("prod_valor_unitario"),
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                ),
                Decimal("0"),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            )
        )["total"]

        ops_por_estado = {
            row["estado"]: row["n"]
            for row in Operacion.objects.values("estado").annotate(n=Count("id"))
        }

        data = {
            "inventario": {
                "total_productos":        productos.count(),
                "agotados":               productos.filter(prod_estado=Producto.Estado.AGOTADO).count(),
                "bajo_stock":             productos.filter(prod_cantidad_disponible__lte=F("prod_stock_minimo")).count(),
                "en_mantenimiento":       productos.filter(prod_cantidad_en_mantenimiento__gt=0).count(),
                "valor_total_disponible": valor_inventario,
            },
            "operaciones": {
                "activas":     ops_por_estado.get(Operacion.EstadoOperacion.ACTIVA, 0),
                "finalizadas": ops_por_estado.get(Operacion.EstadoOperacion.FINALIZADA, 0),
                "canceladas":  ops_por_estado.get(Operacion.EstadoOperacion.CANCELADA, 0),
            },
        }
        return Response(data)