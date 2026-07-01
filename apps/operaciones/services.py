"""
Capa de servicios de OPERACIONES.

Aquí vive la lógica de negocio: crear ventas/préstamos, registrar
devoluciones y cancelar operaciones, ajustando el stock de forma atómica.

Los modelos quedan como simples contenedores de datos (+ validación en
`clean()`); toda la orquestación y los efectos sobre el stock ocurren aquí.
"""
from django.db import transaction

from apps.inventario.models import Producto

from .models import DetalleOperacion, Devolucion, Operacion


@transaction.atomic
def crear_operacion(*, tipo_operacion, usuario, detalles,
                    cliente=None, fecha_devolucion=None, observaciones=None):
    """
    Crea una operación (venta o préstamo) con sus detalles y ajusta el stock.
    `detalles`: lista de dicts {producto, cantidad, precio_unitario}.
    """
    operacion = Operacion.objects.create(
        tipo_operacion=tipo_operacion,
        usuario=usuario,
        cliente=cliente,
        fecha_devolucion=fecha_devolucion,
        observaciones=observaciones,
    )
    for item in detalles:
        agregar_detalle(
            operacion=operacion,
            producto=item["producto"],
            cantidad=item["cantidad"],
            precio_unitario=item["precio_unitario"],
        )
    return operacion


@transaction.atomic
def agregar_detalle(*, operacion, producto, cantidad, precio_unitario):
    """Agrega una línea a la operación y descuenta el stock (con lock)."""
    prod = Producto.objects.select_for_update().get(pk=producto.pk)

    detalle = DetalleOperacion(
        operacion=operacion, producto=prod,
        cantidad=cantidad, precio_unitario=precio_unitario,
    )
    detalle.subtotal = cantidad * precio_unitario
    detalle.full_clean()          # reutiliza la validación del modelo (stock, tipo, cantidad)

    prod.prod_cantidad_disponible -= cantidad
    if operacion.tipo_operacion == Operacion.TipoOperacion.PRESTAMO:
        prod.prod_cantidad_prestada += cantidad
    prod.save()

    detalle.save()
    return detalle


@transaction.atomic
def registrar_devolucion(*, detalle, cantidad_devuelta,
                         estado_devolucion=Devolucion.EstadoDevolucion.BUENO,
                         observaciones=None):
    """
    Registra una devolución (parcial o total) de un préstamo y ajusta el stock
    según el estado en que vuelve la unidad:
      - bueno   → vuelve a disponible
      - dañado  → entra a mantenimiento
      - perdido → pérdida total (no vuelve a ningún contador)
    """
    detalle = DetalleOperacion.objects.select_for_update().get(pk=detalle.pk)

    dev = Devolucion(
        detalle=detalle, cantidad_devuelta=cantidad_devuelta,
        estado_devolucion=estado_devolucion, observaciones=observaciones,
    )
    dev.full_clean()              # reutiliza Devolucion.clean() (solo préstamos, pendiente, etc.)

    producto = Producto.objects.select_for_update().get(pk=detalle.producto_id)
    producto.prod_cantidad_prestada -= cantidad_devuelta
    if estado_devolucion == Devolucion.EstadoDevolucion.BUENO:
        producto.prod_cantidad_disponible += cantidad_devuelta
    elif estado_devolucion == Devolucion.EstadoDevolucion.DAÑADO:
        producto.prod_cantidad_en_mantenimiento += cantidad_devuelta
    # perdido → no vuelve a ningún contador
    producto.save()

    detalle.cantidad_devuelta += cantidad_devuelta
    detalle.save(update_fields=["cantidad_devuelta"])

    dev.save()
    return dev


@transaction.atomic
def cancelar_operacion(operacion):
    """Cancela una operación y devuelve al stock las unidades no devueltas."""
    for detalle in operacion.detalles.select_for_update():
        pendiente = detalle.cantidad - detalle.cantidad_devuelta
        if pendiente <= 0:
            continue
        producto = Producto.objects.select_for_update().get(pk=detalle.producto_id)
        producto.prod_cantidad_disponible += pendiente
        if operacion.tipo_operacion == Operacion.TipoOperacion.PRESTAMO:
            producto.prod_cantidad_prestada -= pendiente
        producto.save()

    operacion.estado = Operacion.EstadoOperacion.CANCELADA
    operacion.save()
    return operacion
