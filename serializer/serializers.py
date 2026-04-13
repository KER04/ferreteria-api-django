# Imports:
from rest_framework import serializers
from django.contrib.auth.models import User
from apps.autenticacion.models import *
from django.contrib.auth import get_user_model
Usuario = get_user_model()

# REGISTRO
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'promedio', 'disponibilidad']

    def create(self, validated_data):
        user = Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
            promedio=validated_data.get('promedio', None),
            disponibilidad=validated_data.get('disponibilidad', True),
        )

        rol_usuario, created = Rol.objects.get_or_create(nombre='Usuario')
        UsuarioRol.objects.create(usuario=user, rol=rol_usuario)

        return user

# USUARIO
class UsuarioSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    rol_id = serializers.IntegerField(source='rol.id', read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'promedio', 'disponibilidad',
            'rol_id', 'rol_nombre', 'roles'
        ]

    def get_roles(self, obj):
        from apps.autenticacion.models import UsuarioRol  # evita import circular
        asignaciones = UsuarioRol.objects.filter(usuario=obj).select_related('rol')
        return [
            {
                "id": ar.rol.id,
                "nombre": ar.rol.nombre
            }
            for ar in asignaciones
        ]

# LOGIN
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

# ROL SIMPLE
class RolSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre']
# ROL COMPLETO
class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion']

# USUARIO X ROL
class UsuarioRolSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all())
    rol = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all())

    class Meta:
        model = UsuarioRol
        fields = ['id', 'usuario', 'rol', 'asignado_en']

#RECURSO
class RecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recurso
        fields = ['id', 'nombre', 'url']

#RECURSOXROL
class RecursoRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecursoRol
        fields = ['id', 'rol', 'recurso', 'asignado_en']




# ══════════════════════════════════════════════════════════════════
# INVENTARIO  —  agregar al final de serializer/serializers.py
# ══════════════════════════════════════════════════════════════════
from apps.inventario.models import TipoCategoria, Marca, Prestamo, Producto
 
 
# ─────────────────────────────────────────────
# TIPO CATEGORÍA
# ─────────────────────────────────────────────
class TipoCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoCategoria
        fields = ["tipr_id", "tipr_nombre"]
 
 
# ─────────────────────────────────────────────
# MARCA
# ─────────────────────────────────────────────
class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Marca
        fields = ["marca_id", "marca_nombre"]
 
 
# ─────────────────────────────────────────────
# PRÉSTAMO
# ─────────────────────────────────────────────
class PrestamoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Prestamo
        fields = ["pres_id", "pres_nombre", "tipo_prestamo"]
 
 
# ─────────────────────────────────────────────
# PRODUCTO — escritura (POST / PUT / PATCH)
# ─────────────────────────────────────────────
class ProductoSerializer(serializers.ModelSerializer):
    # Campos que solo genera/calcula el sistema
    codigo_producto        = serializers.CharField(read_only=True)
    prod_cantidad_prestada = serializers.IntegerField(read_only=True)
    prod_cantidad_total    = serializers.IntegerField(read_only=True)
 
    class Meta:
        model  = Producto
        fields = [
            "prod_id",
            "prod_nombre",
            "prod_modelo",
            "descripcion",
            "proveedor",
            "prod_foto",               # ImageField — acepta multipart/form-data
            "codigo_producto",         # read_only
            "prod_valor_unitario",
            "prod_estado",
            "prod_cantidad_disponible",
            "prod_cantidad_prestada",  # read_only
            "prod_cantidad_total",     # read_only
            "tipo_categoria",
            "marca",
            "prestamo",
        ]
 
    # ── validaciones ─────────────────────────
    def validate_prod_cantidad_disponible(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "La cantidad disponible no puede ser negativa."
            )
        return value
 
    def validate_prod_valor_unitario(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El valor unitario no puede ser negativo."
            )
        return value
 
 
# ─────────────────────────────────────────────
# PRODUCTO — lectura expandida (GET list / retrieve)
# ─────────────────────────────────────────────
class ProductoReadSerializer(serializers.ModelSerializer):
    tipo_categoria_nombre = serializers.StringRelatedField(
        source="tipo_categoria", read_only=True
    )
    marca_nombre    = serializers.StringRelatedField(source="marca",    read_only=True)
    prestamo_nombre = serializers.StringRelatedField(source="prestamo", read_only=True)
    prod_foto_url   = serializers.SerializerMethodField()
 
    class Meta:
        model  = Producto
        fields = [
            "prod_id",
            "prod_nombre",
            "prod_modelo",
            "descripcion",
            "proveedor",
            "prod_foto",
            "prod_foto_url",           # URL absoluta lista para <img src="...">
            "codigo_producto",
            "prod_valor_unitario",
            "prod_estado",
            "prod_cantidad_disponible",
            "prod_cantidad_prestada",
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