from django.contrib import admin

from .models import Recurso, RecursoRol, Rol, Usuario, UsuarioRol

admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(UsuarioRol)
admin.site.register(Recurso)
admin.site.register(RecursoRol)
