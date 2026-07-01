from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from .models import Rol, UsuarioRol, Recurso, RecursoRol

Usuario = get_user_model()


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
        rol_usuario, _ = Rol.objects.get_or_create(nombre='Usuario')
        UsuarioRol.objects.create(usuario=user, rol=rol_usuario)
        return user


class UsuarioSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'first_name', 'last_name', 'promedio', 'disponibilidad', 'roles']

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_roles(self, obj):
        asignaciones = UsuarioRol.objects.filter(usuario=obj).select_related('rol')
        return [{"id": ar.rol.id, "nombre": ar.rol.nombre} for ar in asignaciones]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RolSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre']


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion']


class UsuarioRolSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all())
    rol = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all())

    class Meta:
        model = UsuarioRol
        fields = ['id', 'usuario', 'rol', 'asignado_en']


class RecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recurso
        fields = ['id', 'nombre', 'url']


class RecursoRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecursoRol
        fields = ['id', 'rol', 'recurso', 'asignado_en']
