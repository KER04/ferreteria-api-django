from decimal import Decimal
from rest_framework import serializers
from .models import Operacion, DetalleOperacion, Devolucion
from django.db import models
from django.utils import timezone


# ─────────────────────────────────────────────
# DETALLE — lectura (añade campos de seguimiento)
# ─────────────────────────────────────────────
class DetalleReadSerializer(serializers.ModelSerializer):
    producto_nombre   = serializers.CharField(source="producto.prod_nombre",     read_only=True)
    producto_codigo   = serializers.CharField(source="producto.codigo_producto", read_only=True)
    # Campos calculados por el modelo
    cantidad_pendiente   = serializers.IntegerField(read_only=True)
    devolucion_completa  = serializers.BooleanField(read_only=True)

    class Meta:
        model  = DetalleOperacion
        fields = [
            "id",
            "producto", "producto_nombre", "producto_codigo",
            "cantidad",
            "cantidad_devuelta",    # acumulado
            "cantidad_pendiente",   # calculado: cantidad - cantidad_devuelta
            "devolucion_completa",  # bool
            "precio_unitario",
            "subtotal",
        ]


# ─────────────────────────────────────────────
# DETALLE — escritura
# ─────────────────────────────────────────────
class DetalleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DetalleOperacion
        fields = ["producto", "cantidad", "precio_unitario"]

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que cero.")
        return value

    def validate_precio_unitario(self, value):
        if value < Decimal("0"):
            raise serializers.ValidationError("El precio unitario no puede ser negativo.")
        return value

    def validate(self, attrs):
        producto = attrs["producto"]
        cantidad = attrs["cantidad"]
        if cantidad > producto.prod_cantidad_disponible:
            raise serializers.ValidationError(
                f"Stock insuficiente para '{producto.prod_nombre}'. "
                f"Disponible: {producto.prod_cantidad_disponible}, "
                f"solicitado: {cantidad}."
            )
        return attrs


# ─────────────────────────────────────────────
# OPERACIÓN — escritura con detalles anidados
# ─────────────────────────────────────────────
class OperacionWriteSerializer(serializers.ModelSerializer):
    detalles = DetalleWriteSerializer(many=True)
    # El usuario se toma del token, no del cliente — evita suplantación.
    usuario  = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model  = Operacion
        fields = [
            "tipo_operacion", "usuario", "cliente",
            "fecha_devolucion", "observaciones", "detalles",
        ]

    def validate_detalles(self, detalles):
        if not detalles:
            raise serializers.ValidationError(
                "La operación debe incluir al menos un producto."
            )
        ids = [d["producto"].pk for d in detalles]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "No puedes incluir el mismo producto más de una vez."
            )
        return detalles

    def validate(self, attrs):
        tipo     = attrs.get("tipo_operacion")
        detalles = attrs.get("detalles", [])

        for item in detalles:
            producto  = item["producto"]
            permitida = producto.tipo_operacion_permitida
            if permitida != "mixto" and permitida != tipo:
                raise serializers.ValidationError(
                    f"'{producto.prod_nombre}' solo permite "
                    f"'{producto.get_tipo_operacion_permitida_display()}'."
                )

        if tipo == Operacion.TipoOperacion.VENTA and attrs.get("fecha_devolucion"):
            raise serializers.ValidationError(
                {"fecha_devolucion": "Las ventas no tienen fecha de devolución."}
            )

        # En préstamos, la fecha de devolución no puede ser anterior a hoy
        fecha_dev = attrs.get("fecha_devolucion")
        if tipo == Operacion.TipoOperacion.PRESTAMO and fecha_dev:
            if fecha_dev < timezone.now().date():
                raise serializers.ValidationError(
                    {"fecha_devolucion": "La fecha de devolución no puede estar en el pasado."}
                )

        return attrs

    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles")
        operacion     = Operacion.objects.create(**validated_data)
        for item in detalles_data:
            DetalleOperacion.objects.create(operacion=operacion, **item)
        return operacion

    def update(self, instance, validated_data):
        # El dueño original NUNCA cambia al editar la cabecera.
        validated_data.pop("usuario", None)
        # Los detalles no se modifican por esta vía (protege el stock).
        validated_data.pop("detalles", None)
        return super().update(instance, validated_data)


# ─────────────────────────────────────────────
# OPERACIÓN — lectura
# ─────────────────────────────────────────────
class OperacionReadSerializer(serializers.ModelSerializer):
    detalles       = DetalleReadSerializer(many=True, read_only=True)
    total          = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model  = Operacion
        fields = [
            "id", "codigo_operacion", "tipo_operacion", "estado",
            "usuario", "usuario_nombre", "cliente",
            "fecha_operacion", "fecha_devolucion",
            "observaciones", "total", "detalles",
        ]


# ─────────────────────────────────────────────
# DEVOLUCIÓN — escritura (soporta parciales)
# ─────────────────────────────────────────────
class DevolucionWriteSerializer(serializers.ModelSerializer):
    
    detalle = serializers.PrimaryKeyRelatedField(
        queryset=DetalleOperacion.objects.filter(
            operacion__tipo_operacion="prestamo"
        ).exclude(
            cantidad_devuelta=models.F("cantidad")
        )
    )
    
    class Meta:
        model  = Devolucion
        fields = [
            "detalle", "cantidad_devuelta",
            "estado_devolucion", "observaciones",
        ]

    def validate(self, attrs):
        detalle          = attrs["detalle"]
        cantidad_pedida  = attrs["cantidad_devuelta"]

        # Solo préstamos
        if detalle.operacion.tipo_operacion != Operacion.TipoOperacion.PRESTAMO:
            raise serializers.ValidationError(
                "Solo se pueden registrar devoluciones de préstamos."
            )

        # Validar contra pendiente, NO contra el total original
        pendiente = detalle.cantidad_pendiente
        if pendiente <= 0:
            raise serializers.ValidationError(
                f"El detalle '{detalle}' ya fue devuelto en su totalidad."
            )
        if cantidad_pedida > pendiente:
            raise serializers.ValidationError(
                {"cantidad_devuelta": (
                    f"Solo quedan {pendiente} unidad(es) pendiente(s) "
                    f"de devolución en este detalle."
                )}
            )

        return attrs


# ─────────────────────────────────────────────
# DEVOLUCIÓN — lectura
# ─────────────────────────────────────────────
class DevolucionReadSerializer(serializers.ModelSerializer):
    producto_nombre  = serializers.CharField(
        source="detalle.producto.prod_nombre", read_only=True
    )
    operacion_codigo = serializers.CharField(
        source="detalle.operacion.codigo_operacion", read_only=True
    )
    # Muestra cuánto queda pendiente DESPUÉS de esta devolución
    pendiente_restante = serializers.SerializerMethodField()

    class Meta:
        model  = Devolucion
        fields = [
            "id",
            "detalle", "operacion_codigo", "producto_nombre",
            "cantidad_devuelta",
            "pendiente_restante",
            "estado_devolucion",
            "fecha_devolucion",
            "observaciones",
        ]

    def get_pendiente_restante(self, obj) -> int:
        return obj.detalle.cantidad_pendiente