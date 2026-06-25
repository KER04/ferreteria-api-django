from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.urls import resolve
from apps.autenticacion.models import Recurso, RecursoRol, UsuarioRol

ADMIN_NAMES = {'administrador', 'admin'}


def _es_admin(user) -> bool:
    if not user.is_authenticated:
        return False
    roles = UsuarioRol.objects.filter(usuario=user).select_related('rol')
    return any(r.rol.nombre.lower() in ADMIN_NAMES for r in roles)


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return _es_admin(request.user)


class IsAdminOrReadOnly(BasePermission):
    """
    Lectura (GET/HEAD/OPTIONS) para cualquier usuario autenticado.
    Escritura (POST/PUT/PATCH/DELETE) solo para administradores.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return _es_admin(request.user)
    
class TieneAccesoRecurso(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        path = request.path

        try:
            recurso = Recurso.objects.get(url=path)
        except Recurso.DoesNotExist:
            return False

        roles_usuario = UsuarioRol.objects.filter(usuario=request.user).values_list('rol', flat=True)
        return RecursoRol.objects.filter(recurso=recurso, rol__in=roles_usuario).exists()