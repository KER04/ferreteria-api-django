from django.contrib import admin
from django.utils.html import format_html
from .models import TipoCategoria, Marca, Prestamo, Producto


@admin.register(TipoCategoria)
class TipoCategoriaAdmin(admin.ModelAdmin):
    list_display  = ("tipr_id", "tipr_nombre")
    search_fields = ("tipr_nombre",)
    ordering      = ("tipr_nombre",)


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display  = ("marca_id", "marca_nombre")
    search_fields = ("marca_nombre",)
    ordering      = ("marca_nombre",)


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display  = ("pres_id", "pres_nombre", "tipo_prestamo")
    search_fields = ("pres_nombre", "tipo_prestamo")
    ordering      = ("pres_nombre",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_producto",
        "prod_nombre",
        "prod_modelo",
        "prod_estado",
        "tipo_categoria",
        "marca",
        "prod_cantidad_disponible",
        "prod_cantidad_prestada",
        "prod_cantidad_total",
        "prod_valor_unitario",
        "thumbnail",
    )
    list_filter   = ("prod_estado", "tipo_categoria", "marca")
    search_fields = ("prod_nombre", "codigo_producto", "proveedor")
    ordering      = ("prod_nombre",)

    # Campos de solo lectura — los calcula el modelo
    readonly_fields = (
        "codigo_producto",
        "prod_cantidad_prestada",
        "prod_cantidad_total",
        "thumbnail",
    )

    fieldsets = (
        ("Identificación", {
            "fields": (
                "prod_nombre", "prod_modelo", "codigo_producto",
                "descripcion", "proveedor",
            )
        }),
        ("Imagen", {
            "fields": ("prod_foto", "thumbnail"),
        }),
        ("Stock y estado", {
            "fields": (
                "prod_estado",
                "prod_cantidad_disponible",
                "prod_cantidad_prestada",
                "prod_cantidad_total",
                "prod_valor_unitario",
            )
        }),
        ("Relaciones", {
            "fields": ("tipo_categoria", "marca", "prestamo"),
        }),
    )

    @admin.display(description="Vista previa")
    def thumbnail(self, obj):
        if obj.prod_foto:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:4px;" />',
                obj.prod_foto.url,
            )
        return "—"