"""
Capa de servicios de MANTENIMIENTO.

Orquesta la entrada de productos a mantenimiento, su salida (recuperados /
dados de baja) y la cancelación, ajustando el stock de forma atómica.
Los modelos quedan como datos + validación (`clean()`).
"""
from django.db import transaction
from django.utils import timezone

from apps.inventario.models import Producto

from .models import Mantenimiento, SalidaMantenimiento


@transaction.atomic
def ingresar_mantenimiento(*, producto, tipo_mantenimiento, cantidad_ingresada,
                           usuario, mant_descripcion=None, costo=None):
    """Ingresa unidades a mantenimiento y las descuenta del stock disponible."""
    prod = Producto.objects.select_for_update().get(pk=producto.pk)

    mant = Mantenimiento(
        producto=prod, tipo_mantenimiento=tipo_mantenimiento,
        cantidad_ingresada=cantidad_ingresada, usuario=usuario,
        mant_descripcion=mant_descripcion, costo=costo,
    )
    mant.full_clean()             # valida cantidad > 0 y stock suficiente

    prod.prod_cantidad_disponible       -= cantidad_ingresada
    prod.prod_cantidad_en_mantenimiento += cantidad_ingresada
    if prod.prod_cantidad_disponible == 0:
        prod.prod_estado = Producto.Estado.MANTENIMIENTO
    prod.save()

    mant.save()
    return mant


@transaction.atomic
def registrar_salida(*, mantenimiento, cantidad_recuperada, cantidad_baja=0,
                     observaciones=None, costo=None):
    """
    Cierra un mantenimiento: las recuperadas vuelven al stock, las dadas de
    baja se pierden. El mantenimiento queda 'Finalizado'.
    """
    mant = Mantenimiento.objects.select_for_update().get(pk=mantenimiento.pk)

    salida = SalidaMantenimiento(
        mantenimiento=mant, cantidad_recuperada=cantidad_recuperada,
        cantidad_baja=cantidad_baja, observaciones=observaciones, costo=costo,
    )
    salida.full_clean()           # valida no-finalizado, total > 0 y total <= ingresadas

    producto = Producto.objects.select_for_update().get(pk=mant.producto_id)
    producto.prod_cantidad_en_mantenimiento -= mant.cantidad_ingresada
    producto.prod_cantidad_disponible       += cantidad_recuperada
    # cantidad_baja se pierde — no vuelve al stock
    if producto.prod_cantidad_disponible == 0:
        producto.prod_estado = Producto.Estado.AGOTADO
    elif producto.prod_estado == Producto.Estado.MANTENIMIENTO:
        producto.prod_estado = Producto.Estado.DISPONIBLE
    producto.save()

    mant.estado              = Mantenimiento.Estado.FINALIZADO
    mant.cantidad_recuperada = cantidad_recuperada
    mant.cantidad_baja       = cantidad_baja
    mant.fecha_salida        = timezone.now().date()
    mant.save(update_fields=[
        "estado", "cantidad_recuperada", "cantidad_baja", "fecha_salida",
    ])

    salida.save()
    return salida


@transaction.atomic
def cancelar_mantenimiento(mantenimiento):
    """Cancela un mantenimiento en proceso y devuelve el stock retenido."""
    mant     = Mantenimiento.objects.select_for_update().get(pk=mantenimiento.pk)
    producto = Producto.objects.select_for_update().get(pk=mant.producto_id)

    pendiente = mant.cantidad_pendiente          # ingresada - recuperada - baja
    producto.prod_cantidad_en_mantenimiento -= pendiente
    producto.prod_cantidad_disponible       += pendiente
    if producto.prod_estado == Producto.Estado.MANTENIMIENTO:
        producto.prod_estado = Producto.Estado.DISPONIBLE
    producto.save()

    mant.estado       = Mantenimiento.Estado.CANCELADO
    mant.fecha_salida = timezone.now().date()
    mant.save(update_fields=["estado", "fecha_salida"])
    return mant
