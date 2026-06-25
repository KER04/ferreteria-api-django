from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from apps.autenticacion.permissions import IsAdminOrReadOnly

from .models import Costo, TipoMantenimiento, Mantenimiento, SalidaMantenimiento
from .serializers import (
    CostoSerializer,
    TipoMantenimientoSerializer,
    MantenimientoWriteSerializer,
    MantenimientoReadSerializer,
    SalidaWriteSerializer,
    SalidaReadSerializer,
)


# ─────────────────────────────────────────────
# COSTO
# ─────────────────────────────────────────────
class CostoViewSet(viewsets.ModelViewSet):
    queryset           = Costo.objects.all().order_by("-cost_id")
    serializer_class   = CostoSerializer
    permission_classes = [IsAdminOrReadOnly]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────
# TIPO MANTENIMIENTO
# ─────────────────────────────────────────────
class TipoMantenimientoViewSet(viewsets.ModelViewSet):
    queryset           = TipoMantenimiento.objects.all().order_by("tima_nombre")
    serializer_class   = TipoMantenimientoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ["tima_nombre"]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─────────────────────────────────────────────
# MANTENIMIENTO
# ─────────────────────────────────────────────
class MantenimientoViewSet(viewsets.ModelViewSet):
    queryset = (
        Mantenimiento.objects
        .select_related(
            "producto", "tipo_mantenimiento",
            "usuario", "costo",
        )
        .prefetch_related("salida")
        .all()
    )
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = [
        "producto__prod_nombre",
        "producto__codigo_producto",
        "estado",
    ]
    ordering_fields    = ["fecha_ingreso", "estado", "mant_id"]

    def get_queryset(self):
        qs = super().get_queryset()
        p  = self.request.query_params

        if estado   := p.get("estado"):
            qs = qs.filter(estado=estado)
        if producto := p.get("producto"):
            qs = qs.filter(producto__prod_id=producto)

        return qs

    def get_serializer_class(self):
        return (
            MantenimientoReadSerializer
            if self.action in ["list", "retrieve"]
            else MantenimientoWriteSerializer
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def list(self, request, *args, **kwargs):
        qs   = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser  = MantenimientoReadSerializer(
            page or qs, many=True,
            context=self.get_serializer_context(),
        )
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        ser = MantenimientoReadSerializer(
            self.get_object(),
            context=self.get_serializer_context(),
        )
        return Response(ser.data)

    def create(self, request, *args, **kwargs):
        ser = MantenimientoWriteSerializer(
            data=request.data,
            context=self.get_serializer_context(),
        )
        ser.is_valid(raise_exception=True)
        mant = ser.save()
        out  = MantenimientoReadSerializer(
            mant, context=self.get_serializer_context()
        )
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Solo permite actualizar descripción y costo mientras está en proceso."""
        instance = self.get_object()
        if instance.estado == Mantenimiento.Estado.FINALIZADO:
            return Response(
                {"detail": "No se puede modificar un mantenimiento finalizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        campos = {"mant_descripcion", "costo"}
        data   = {k: v for k, v in request.data.items() if k in campos}
        ser    = MantenimientoWriteSerializer(
            instance, data=data, partial=True,
            context=self.get_serializer_context(),
        )
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = MantenimientoReadSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(out.data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Un mantenimiento en proceso retiene stock; debe cancelarse primero
        # para devolver las unidades. Solo los cancelados pueden borrarse.
        if instance.estado == Mantenimiento.Estado.EN_PROCESO:
            return Response(
                {"detail": "No se puede eliminar un mantenimiento en proceso. Cancélalo primero."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if instance.estado == Mantenimiento.Estado.FINALIZADO:
            return Response(
                {"detail": "No se puede eliminar un mantenimiento finalizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── acción: registrar salida (finalizar) ──
    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar(self, request, pk=None):
        mant = self.get_object()

        if mant.estado == Mantenimiento.Estado.FINALIZADO:
            return Response(
                {"detail": "Este mantenimiento ya fue finalizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Inyectar el mantenimiento en los datos
        data = {**request.data, "mantenimiento": mant.pk}
        ser  = SalidaWriteSerializer(data=data)
        ser.is_valid(raise_exception=True)
        salida = ser.save()

        out = MantenimientoReadSerializer(
            Mantenimiento.objects.get(pk=mant.pk),
            context=self.get_serializer_context(),
        )
        return Response(out.data, status=status.HTTP_200_OK)

    # ── acción: cancelar (devuelve el stock retenido) ──
    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        from django.db import transaction
        from apps.inventario.models import Producto

        mant = self.get_object()
        if mant.estado != Mantenimiento.Estado.EN_PROCESO:
            return Response(
                {"detail": f"Solo se pueden cancelar mantenimientos en proceso "
                           f"(estado actual: '{mant.estado}')."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            mant     = Mantenimiento.objects.select_for_update().get(pk=mant.pk)
            producto = Producto.objects.select_for_update().get(pk=mant.producto_id)

            # Devolver al stock las unidades aún en mantenimiento
            pendiente = mant.cantidad_pendiente   # ingresada - recuperada - baja
            producto.prod_cantidad_en_mantenimiento -= pendiente
            producto.prod_cantidad_disponible       += pendiente

            # Si el producto había quedado marcado en mantenimiento, liberarlo
            if producto.prod_estado == Producto.Estado.MANTENIMIENTO:
                producto.prod_estado = Producto.Estado.DISPONIBLE
            producto.save()

            mant.estado       = Mantenimiento.Estado.CANCELADO
            mant.fecha_salida = timezone.now().date()
            mant.save(update_fields=["estado", "fecha_salida"])

        out = MantenimientoReadSerializer(
            Mantenimiento.objects.get(pk=mant.pk),
            context=self.get_serializer_context(),
        )
        return Response(out.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# SALIDA MANTENIMIENTO (consulta directa)
# ─────────────────────────────────────────────
class SalidaMantenimientoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Solo lectura — las salidas se crean desde
    POST /mantenimientos/{id}/finalizar/
    """
    queryset = (
        SalidaMantenimiento.objects
        .select_related("mantenimiento__producto", "costo")
        .all()
        .order_by("-fecha_salida")
    )
    serializer_class   = SalidaReadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.OrderingFilter]
    ordering_fields    = ["fecha_salida", "id"]