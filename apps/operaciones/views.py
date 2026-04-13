from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .models import Operacion, DetalleOperacion, Devolucion
from .serializers import (
    OperacionWriteSerializer,
    OperacionReadSerializer,
    DevolucionWriteSerializer,
    DevolucionReadSerializer,
)


# ─────────────────────────────────────────────
# OPERACIÓN
# ─────────────────────────────────────────────
class OperacionViewSet(viewsets.ModelViewSet):
    queryset = (
        Operacion.objects
        .select_related("usuario")
        .prefetch_related("detalles__producto")
        .all()
    )
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ["cliente", "tipo_operacion", "codigo_operacion", "usuario__username"]
    ordering_fields    = ["fecha_operacion", "tipo_operacion", "estado", "id"]

    def get_queryset(self):
        qs = super().get_queryset()
        p  = self.request.query_params

        if tipo   := p.get("tipo_operacion"):
            qs = qs.filter(tipo_operacion=tipo)
        if estado := p.get("estado"):
            qs = qs.filter(estado=estado)
        if fecha  := p.get("fecha_operacion"):
            qs = qs.filter(fecha_operacion=fecha)

        return qs

    def get_serializer_class(self):
        return OperacionReadSerializer if self.action in ["list", "retrieve"] else OperacionWriteSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def list(self, request, *args, **kwargs):
        qs   = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser  = OperacionReadSerializer(
            page or qs, many=True, context=self.get_serializer_context()
        )
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        ser = OperacionReadSerializer(
            self.get_object(), context=self.get_serializer_context()
        )
        return Response(ser.data)

    def create(self, request, *args, **kwargs):
        ser = OperacionWriteSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        ser.is_valid(raise_exception=True)
        operacion = ser.save()
        out = OperacionReadSerializer(operacion, context=self.get_serializer_context())
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Solo permite actualizar campos de cabecera (estado, observaciones, cliente).
        Los detalles NO se modifican por aquí para proteger la integridad del stock.
        """
        instance = self.get_object()
        # Campos actualizables de la cabecera
        campos_permitidos = {"estado", "observaciones", "cliente", "fecha_devolucion"}
        data_filtrada = {k: v for k, v in request.data.items() if k in campos_permitidos}
        ser = OperacionWriteSerializer(
            instance, data=data_filtrada, partial=True,
            context=self.get_serializer_context()
        )
        ser.is_valid(raise_exception=True)
        instance = ser.save()
        out = OperacionReadSerializer(instance, context=self.get_serializer_context())
        return Response(out.data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.estado == Operacion.EstadoOperacion.ACTIVA:
            return Response(
                {"detail": "No se puede eliminar una operación activa. Cancélala primero."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── acción extra: ver detalles de una operación ──
    @action(detail=True, methods=["get"], url_path="detalles")
    def detalles(self, request, pk=None):
        operacion = self.get_object()
        from .serializers import DetalleReadSerializer
        ser = DetalleReadSerializer(
            operacion.detalles.select_related("producto").all(),
            many=True,
        )
        return Response(ser.data)

    # ── acción extra: cancelar operación ────────────
    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        operacion = self.get_object()
        if operacion.estado != Operacion.EstadoOperacion.ACTIVA:
            return Response(
                {"detail": f"La operación ya está en estado '{operacion.estado}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        operacion.estado = Operacion.EstadoOperacion.CANCELADA
        operacion.save()
        return Response({"detail": f"Operación {operacion.codigo_operacion} cancelada."})

    # ── acción extra: finalizar operación ───────────
    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar(self, request, pk=None):
        operacion = self.get_object()
        if operacion.estado != Operacion.EstadoOperacion.ACTIVA:
            return Response(
                {"detail": f"La operación ya está en estado '{operacion.estado}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        operacion.estado = Operacion.EstadoOperacion.FINALIZADA
        operacion.save()
        return Response({"detail": f"Operación {operacion.codigo_operacion} finalizada."})


# ─────────────────────────────────────────────
# DEVOLUCIÓN
# ─────────────────────────────────────────────
class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = (
        Devolucion.objects
        .select_related(
            "detalle__operacion",
            "detalle__producto",
        )
        .all()
        .order_by("-fecha_devolucion", "-id")
    )
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ["detalle__producto__prod_nombre", "detalle__operacion__codigo_operacion"]
    ordering_fields    = ["fecha_devolucion", "id"]

    def get_serializer_class(self):
        return DevolucionReadSerializer if self.action in ["list", "retrieve"] else DevolucionWriteSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def list(self, request, *args, **kwargs):
        qs   = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        ser  = DevolucionReadSerializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        return Response(DevolucionReadSerializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        ser = DevolucionWriteSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        ser.is_valid(raise_exception=True)
        devolucion = ser.save()
        out = DevolucionReadSerializer(devolucion)
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Las devoluciones no se pueden modificar una vez registradas."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Las devoluciones no se pueden eliminar."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )