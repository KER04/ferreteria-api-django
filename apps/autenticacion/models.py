# Importaciones:
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

#time stamped
class TimeStampedModel(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

#rol
class Rol(models.Model):
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.nombre


#user
class Usuario(TimeStampedModel, AbstractUser):
    promedio = models.FloatField(null=True, blank=True, verbose_name="Promedio académico", help_text="Promedio del usuario (si aplica)")
    disponibilidad = models.BooleanField(default=True, verbose_name="¿Está disponible?", help_text="Indica si el usuario está disponible")

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuarios"

    def __str__(self):
        return f"{self.username} - {self.first_name} {self.last_name}"
 
#usuario_rol
class UsuarioRol(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='roles_asignados')
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='usuarios_asignados')
    asignado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asignación de Rol"
        verbose_name_plural = "Asignaciones de Roles"
        unique_together = ['usuario', 'rol']

    def __str__(self):
        return f"{self.usuario} → {self.rol}"
    
class Recurso(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre legible del recurso")
    url = models.CharField(max_length=255, unique=True, help_text="Ruta del backend sin dominio, ej: /api/entrenamientos/")

    def __str__(self):
        return f"{self.nombre} ({self.url})"
    
class RecursoRol(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name="recursos")
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE, related_name="roles")
    asignado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('rol', 'recurso')

    def __str__(self):
        return f"{self.rol.nombre} → {self.recurso.url}"