from rest_framework.permissions import BasePermission
from django.urls import resolve
from apps.autenticacion.models import Recurso, RecursoRol, UsuarioRol

class IsAdminRole(BasePermission):
    ADMIN_NAMES = ['administrador', 'Administrador', 'Admin', 'admin']

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False

        roles = UsuarioRol.objects.filter(usuario=user).select_related('rol')
        nombres_roles = [r.rol.nombre.lower() for r in roles]
        return any(nombre in self.ADMIN_NAMES for nombre in nombres_roles)
    
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