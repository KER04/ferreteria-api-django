from django.contrib import admin

from .models import Costo, Mantenimiento, SalidaMantenimiento, TipoMantenimiento


@admin.register(Costo)
class CostoAdmin(admin.ModelAdmin):
    list_display  = ("cost_id", "cost_total", "cost_partes_afectadas", "cost_fecha_pago")
    ordering      = ("-cost_id",)


@admin.register(TipoMantenimiento)
class TipoMantenimientoAdmin(admin.ModelAdmin):
    list_display  = ("tima_id", "tima_nombre")
    search_fields = ("tima_nombre",)


class SalidaInline(admin.StackedInline):
    model       = SalidaMantenimiento
    extra       = 0
    readonly_fields = ("fecha_salida",)
    fields      = (
        "cantidad_recuperada", "cantidad_baja",
        "observaciones", "costo", "fecha_salida",
    )


@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display  = (
        "mant_id", "producto", "tipo_mantenimiento",
        "estado", "cantidad_ingresada", "cantidad_recuperada",
        "cantidad_baja", "fecha_ingreso", "fecha_salida",
    )
    list_filter   = ("estado", "tipo_mantenimiento", "fecha_ingreso")
    search_fields = ("producto__prod_nombre", "producto__codigo_producto")
    readonly_fields = (
        "fecha_ingreso", "estado",
        "cantidad_recuperada", "cantidad_baja", "fecha_salida",
    )
    inlines       = [SalidaInline]


@admin.register(SalidaMantenimiento)
class SalidaMantenimientoAdmin(admin.ModelAdmin):
    list_display  = (
        "id", "mantenimiento", "cantidad_recuperada",
        "cantidad_baja", "fecha_salida",
    )
    readonly_fields = ("fecha_salida",)
