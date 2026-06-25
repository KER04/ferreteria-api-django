from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.inventario.models import TipoCategoria, Marca, Prestamo, Producto
from apps.operaciones.models import Operacion, DetalleOperacion, Devolucion

Usuario = get_user_model()


def crear_producto(disponible=10, permitida=Producto.TipoOperacionPermitida.MIXTO):
    categoria = TipoCategoria.objects.create(tipr_nombre="Herramientas")
    marca     = Marca.objects.create(marca_nombre="Truper")
    prestamo  = Prestamo.objects.create(pres_nombre="Estándar", tipo_prestamo="interno")
    return Producto.objects.create(
        prod_nombre="Taladro",
        prod_valor_unitario=Decimal("100.00"),
        prod_cantidad_disponible=disponible,
        tipo_operacion_permitida=permitida,
        tipo_categoria=categoria,
        marca=marca,
        prestamo=prestamo,
    )


class StockOperacionesTests(TestCase):
    def setUp(self):
        self.usuario  = Usuario.objects.create_user(username="empleado", password="x")
        self.producto = crear_producto(disponible=10)

    def _operacion(self, tipo):
        return Operacion.objects.create(tipo_operacion=tipo, usuario=self.usuario)

    # ── ventas ───────────────────────────────
    def test_venta_descuenta_disponible(self):
        op = self._operacion(Operacion.TipoOperacion.VENTA)
        DetalleOperacion.objects.create(
            operacion=op, producto=self.producto,
            cantidad=3, precio_unitario=Decimal("100.00"),
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 7)
        self.assertEqual(self.producto.prod_cantidad_prestada, 0)

    def test_stock_insuficiente_lanza_error(self):
        op = self._operacion(Operacion.TipoOperacion.VENTA)
        with self.assertRaises(ValidationError):
            DetalleOperacion.objects.create(
                operacion=op, producto=self.producto,
                cantidad=999, precio_unitario=Decimal("100.00"),
            )

    # ── préstamos ────────────────────────────
    def test_prestamo_mueve_a_prestada(self):
        op = self._operacion(Operacion.TipoOperacion.PRESTAMO)
        DetalleOperacion.objects.create(
            operacion=op, producto=self.producto,
            cantidad=4, precio_unitario=Decimal("0.00"),
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 6)
        self.assertEqual(self.producto.prod_cantidad_prestada, 4)

    # ── devoluciones ─────────────────────────
    def test_devolucion_parcial_ajusta_stock(self):
        op = self._operacion(Operacion.TipoOperacion.PRESTAMO)
        det = DetalleOperacion.objects.create(
            operacion=op, producto=self.producto,
            cantidad=4, precio_unitario=Decimal("0.00"),
        )
        Devolucion.objects.create(detalle=det, cantidad_devuelta=2)

        self.producto.refresh_from_db()
        det.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 8)
        self.assertEqual(self.producto.prod_cantidad_prestada, 2)
        self.assertEqual(det.cantidad_devuelta, 2)
        self.assertEqual(det.cantidad_pendiente, 2)

    def test_devolucion_no_excede_pendiente(self):
        op = self._operacion(Operacion.TipoOperacion.PRESTAMO)
        det = DetalleOperacion.objects.create(
            operacion=op, producto=self.producto,
            cantidad=4, precio_unitario=Decimal("0.00"),
        )
        with self.assertRaises(ValidationError):
            Devolucion.objects.create(detalle=det, cantidad_devuelta=5)


class CancelarOperacionTests(TestCase):
    def setUp(self):
        self.usuario  = Usuario.objects.create_user(username="empleado", password="x")
        self.producto = crear_producto(disponible=10)
        self.client   = APIClient()
        self.client.force_authenticate(user=self.usuario)

    def test_cancelar_venta_revierte_stock(self):
        op = Operacion.objects.create(
            tipo_operacion=Operacion.TipoOperacion.VENTA, usuario=self.usuario,
        )
        DetalleOperacion.objects.create(
            operacion=op, producto=self.producto,
            cantidad=3, precio_unitario=Decimal("100.00"),
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 7)

        resp = self.client.post(f"/api/operaciones/operaciones/{op.id}/cancelar/")
        self.assertEqual(resp.status_code, 200)

        op.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertEqual(op.estado, Operacion.EstadoOperacion.CANCELADA)
        self.assertEqual(self.producto.prod_cantidad_disponible, 10)

    def test_cancelar_prestamo_con_devolucion_parcial(self):
        op = Operacion.objects.create(
            tipo_operacion=Operacion.TipoOperacion.PRESTAMO, usuario=self.usuario,
        )
        det = DetalleOperacion.objects.create(
            operacion=op, producto=self.producto,
            cantidad=4, precio_unitario=Decimal("0.00"),
        )
        Devolucion.objects.create(detalle=det, cantidad_devuelta=1)

        # Cancela: solo deben volver las 3 unidades aún prestadas
        resp = self.client.post(f"/api/operaciones/operaciones/{op.id}/cancelar/")
        self.assertEqual(resp.status_code, 200)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 10)
        self.assertEqual(self.producto.prod_cantidad_prestada, 0)
