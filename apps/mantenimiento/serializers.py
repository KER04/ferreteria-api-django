from rest_framework import serializers
from .models import Costo, TipoMantenimiento, Mantenimiento, SalidaMantenimiento


# ─────────────────────────────────────────────
# COSTO
# ─────────────────────────────────────────────
class CostoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Costo
        fields = [
            "cost_id", "cost_total",
            "cost_partes_afectadas", "cost_fecha_pago",
        ]

    def validate_cost_total(self, value):
        if value < 0:
            raise serializers.ValidationError("El costo no puede ser negativo.")
        return value


# ─────────────────────────────────────────────
# TIPO MANTENIMIENTO
# ─────────────────────────────────────────────
class TipoMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoMantenimiento
        fields = ["tima_id", "tima_nombre"]


# ─────────────────────────────────────────────
# SALIDA — escritura
# ─────────────────────────────────────────────
class SalidaWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SalidaMantenimiento
        fields = [
            "mantenimiento",
            "cantidad_recuperada",
            "cantidad_baja",
            "observaciones",
            "costo",
        ]

    def validate(self, attrs):
        mant   = attrs["mantenimiento"]
        total  = attrs["cantidad_recuperada"] + attrs.get("cantidad_baja", 0)

        if mant.estado == Mantenimiento.Estado.FINALIZADO:
            raise serializers.ValidationError(
                "Este mantenimiento ya fue finalizado."
            )
        if total <= 0:
            raise serializers.ValidationError(
                "Debes indicar al menos una unidad recuperada o dada de baja."
            )
        if total > mant.cantidad_ingresada:
            raise serializers.ValidationError(
                f"Recuperadas + bajas ({total}) no puede superar "
                f"las ingresadas ({mant.cantidad_ingresada})."
            )
        return attrs


# ─────────────────────────────────────────────
# SALIDA — lectura
# ─────────────────────────────────────────────
class SalidaReadSerializer(serializers.ModelSerializer):
    costo_info = CostoSerializer(source="costo", read_only=True)

    class Meta:
        model  = SalidaMantenimiento
        fields = [
            "id",
            "mantenimiento",
            "fecha_salida",
            "cantidad_recuperada",
            "cantidad_baja",
            "observaciones",
            "costo", "costo_info",
        ]


# ─────────────────────────────────────────────
# MANTENIMIENTO — escritura (entrada)
# ─────────────────────────────────────────────
class MantenimientoWriteSerializer(serializers.ModelSerializer):
    # El usuario se toma del token, no del cliente — evita suplantación.
    usuario = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model  = Mantenimiento
        fields = [
            "producto",
            "tipo_mantenimiento",
            "cantidad_ingresada",
            "mant_descripcion",
            "usuario",
            "costo",
        ]

    def validate_cantidad_ingresada(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "La cantidad debe ser mayor que cero."
            )
        return value

    def update(self, instance, validated_data):
        # El dueño original NUNCA cambia al editar.
        validated_data.pop("usuario", None)
        return super().update(instance, validated_data)

    def validate(self, attrs):
        producto  = attrs["producto"]
        cantidad  = attrs["cantidad_ingresada"]
        if cantidad > producto.prod_cantidad_disponible:
            raise serializers.ValidationError(
                {"cantidad_ingresada": (
                    f"Stock insuficiente. Disponible: "
                    f"{producto.prod_cantidad_disponible}, "
                    f"solicitado: {cantidad}."
                )}
            )
        return attrs


# ─────────────────────────────────────────────
# MANTENIMIENTO — lectura expandida
# ─────────────────────────────────────────────
class MantenimientoReadSerializer(serializers.ModelSerializer):
    producto_nombre        = serializers.CharField(
        source="producto.prod_nombre", read_only=True
    )
    producto_codigo        = serializers.CharField(
        source="producto.codigo_producto", read_only=True
    )
    tipo_mantenimiento_nombre = serializers.CharField(
        source="tipo_mantenimiento.tima_nombre", read_only=True
    )
    usuario_nombre         = serializers.CharField(
        source="usuario.username", read_only=True
    )
    cantidad_pendiente     = serializers.IntegerField(read_only=True)
    costo_info             = CostoSerializer(source="costo", read_only=True)
    salida                 = SalidaReadSerializer(read_only=True)

    class Meta:
        model  = Mantenimiento
        fields = [
            "mant_id",
            "estado",
            "producto", "producto_nombre", "producto_codigo",
            "tipo_mantenimiento", "tipo_mantenimiento_nombre",
            "cantidad_ingresada",
            "cantidad_recuperada",
            "cantidad_baja",
            "cantidad_pendiente",
            "mant_descripcion",
            "fecha_ingreso",
            "fecha_salida",
            "usuario", "usuario_nombre",
            "costo", "costo_info",
            "salida",             # detalle completo de la salida si ya finalizó
        ]