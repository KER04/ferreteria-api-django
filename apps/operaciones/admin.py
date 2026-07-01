from django.contrib import admin

from .models import DetalleOperacion, Devolucion, Operacion


class DetalleOperacionInline(admin.TabularInline):
    model       = DetalleOperacion
    extra       = 1
    readonly_fields = ("subtotal",)
    fields      = ("producto", "cantidad", "precio_unitario", "subtotal")


@admin.register(Operacion)
class OperacionAdmin(admin.ModelAdmin):
    list_display    = (
        "codigo_operacion", "tipo_operacion", "estado",
        "usuario", "cliente", "fecha_operacion", "total_display",
    )
    list_filter     = ("tipo_operacion", "estado", "fecha_operacion")
    search_fields   = ("codigo_operacion", "cliente", "usuario__username")
    readonly_fields = ("codigo_operacion", "fecha_operacion")
    inlines         = [DetalleOperacionInline]

    fieldsets = (
        ("Identificación", {
            "fields": ("codigo_operacion", "tipo_operacion", "estado"),
        }),
        ("Partes", {
            "fields": ("usuario", "cliente"),
        }),
        ("Fechas", {
            "fields": ("fecha_operacion", "fecha_devolucion"),
        }),
        ("Extras", {
            "fields": ("observaciones",),
        }),
    )

    @admin.display(description="Total")
    def total_display(self, obj):
        return f"${obj.total:,.2f}"


@admin.register(DetalleOperacion)
class DetalleOperacionAdmin(admin.ModelAdmin):
    list_display  = ("operacion", "producto", "cantidad", "precio_unitario", "subtotal")
    list_filter   = ("operacion__tipo_operacion",)
    search_fields = ("operacion__codigo_operacion", "producto__prod_nombre")
    readonly_fields = ("subtotal",)


@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display  = (
        "detalle", "cantidad_devuelta",
        "estado_devolucion", "fecha_devolucion",
    )
    list_filter   = ("estado_devolucion", "fecha_devolucion")
    search_fields = (
        "detalle__operacion__codigo_operacion",
        "detalle__producto__prod_nombre",
    )
    readonly_fields = ("fecha_devolucion",)
