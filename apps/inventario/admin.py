from django.contrib import admin
from .models import TipoCategoria, Marca, Prestamo, Producto

admin.site.register(TipoCategoria)
admin.site.register(Marca)
admin.site.register(Prestamo)
admin.site.register(Producto)
