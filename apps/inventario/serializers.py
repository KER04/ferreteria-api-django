from rest_framework import serializers
from .models import TipoCategoria, Marca, Prestamo, Producto


class TipoCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCategoria
        fields = ["tipr_id", "tipr_nombre"]


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ["marca_id", "marca_nombre"]


class PrestamoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prestamo
        fields = ["pres_id", "pres_nombre", "tipo_prestamo"]


class ProductoSerializer(serializers.ModelSerializer):
    codigo_producto                = serializers.CharField(read_only=True)
    prod_cantidad_prestada         = serializers.IntegerField(read_only=True)
    prod_cantidad_en_mantenimiento = serializers.IntegerField(read_only=True)
    prod_cantidad_total            = serializers.IntegerField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            "prod_id",
            "prod_nombre",
            "prod_modelo",
            "descripcion",
            "proveedor",
            "prod_foto",
            "codigo_producto",
            "tipo_operacion_permitida",
            "prod_valor_unitario",
            "prod_estado",
            "prod_cantidad_disponible",
            "prod_cantidad_prestada",
            "prod_cantidad_en_mantenimiento",
            "prod_cantidad_total",
            "tipo_categoria",
            "marca",
            "prestamo",
        ]

    def validate_prod_cantidad_disponible(self, value):
        if value < 0:
            raise serializers.ValidationError("La cantidad disponible no puede ser negativa.")
        return value

    def validate_prod_valor_unitario(self, value):
        if value < 0:
            raise serializers.ValidationError("El valor unitario no puede ser negativo.")
        return value


class ProductoReadSerializer(serializers.ModelSerializer):
    tipo_categoria_nombre = serializers.StringRelatedField(source="tipo_categoria", read_only=True)
    marca_nombre          = serializers.StringRelatedField(source="marca",          read_only=True)
    prestamo_nombre       = serializers.StringRelatedField(source="prestamo",       read_only=True)
    prod_foto_url         = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            "prod_id",
            "prod_nombre",
            "prod_modelo",
            "descripcion",
            "proveedor",
            "prod_foto",
            "prod_foto_url",
            "codigo_producto",
            "tipo_operacion_permitida",
            "prod_valor_unitario",
            "prod_estado",
            "prod_cantidad_disponible",
            "prod_cantidad_prestada",
            "prod_cantidad_en_mantenimiento",
            "prod_cantidad_total",
            "tipo_categoria",
            "tipo_categoria_nombre",
            "marca",
            "marca_nombre",
            "prestamo",
            "prestamo_nombre",
        ]

    def get_prod_foto_url(self, obj) -> str | None:
        if not obj.prod_foto:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.prod_foto.url) if request else obj.prod_foto.url
