from django.contrib import admin
from .models import Renta, TipoPago, Estado, Pago, RentaProducto

admin.site.register(Renta)
admin.site.register(TipoPago)
admin.site.register(Estado)
admin.site.register(Pago)
admin.site.register(RentaProducto)
