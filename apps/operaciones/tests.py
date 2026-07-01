from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.inventario.models import Marca, Prestamo, Producto, TipoCategoria
from apps.operaciones import services
from apps.operaciones.models import DetalleOperacion, Devolucion, Operacion

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

    def _crear_op(self, tipo, cantidad, precio="0.00"):
        return services.crear_operacion(
            tipo_operacion=tipo, usuario=self.usuario,
            detalles=[{
                "producto": self.producto,
                "cantidad": cantidad,
                "precio_unitario": Decimal(precio),
            }],
        )

    # ── ventas ───────────────────────────────
    def test_venta_descuenta_disponible(self):
        self._crear_op(Operacion.TipoOperacion.VENTA, 3, "100.00")
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 7)
        self.assertEqual(self.producto.prod_cantidad_prestada, 0)

    def test_stock_insuficiente_lanza_error(self):
        with self.assertRaises(ValidationError):
            self._crear_op(Operacion.TipoOperacion.VENTA, 999, "100.00")

    # ── préstamos ────────────────────────────
    def test_prestamo_mueve_a_prestada(self):
        self._crear_op(Operacion.TipoOperacion.PRESTAMO, 4)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 6)
        self.assertEqual(self.producto.prod_cantidad_prestada, 4)

    # ── devoluciones ─────────────────────────
    def test_devolucion_parcial_ajusta_stock(self):
        op  = self._crear_op(Operacion.TipoOperacion.PRESTAMO, 4)
        det = op.detalles.first()
        services.registrar_devolucion(detalle=det, cantidad_devuelta=2)

        self.producto.refresh_from_db()
        det.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 8)
        self.assertEqual(self.producto.prod_cantidad_prestada, 2)
        self.assertEqual(det.cantidad_devuelta, 2)
        self.assertEqual(det.cantidad_pendiente, 2)

    def test_devolucion_no_excede_pendiente(self):
        op  = self._crear_op(Operacion.TipoOperacion.PRESTAMO, 4)
        det = op.detalles.first()
        with self.assertRaises(ValidationError):
            services.registrar_devolucion(detalle=det, cantidad_devuelta=5)

    def test_devolucion_danada_va_a_mantenimiento(self):
        op  = self._crear_op(Operacion.TipoOperacion.PRESTAMO, 4)
        det = op.detalles.first()
        services.registrar_devolucion(
            detalle=det, cantidad_devuelta=2,
            estado_devolucion=Devolucion.EstadoDevolucion.DAÑADO,
        )
        self.producto.refresh_from_db()
        # Las 2 dañadas NO vuelven a disponible; van a mantenimiento
        self.assertEqual(self.producto.prod_cantidad_disponible, 6)   # 10 - 4 prestadas
        self.assertEqual(self.producto.prod_cantidad_en_mantenimiento, 2)
        self.assertEqual(self.producto.prod_cantidad_prestada, 2)

    def test_devolucion_perdida_reduce_total(self):
        op  = self._crear_op(Operacion.TipoOperacion.PRESTAMO, 4)
        det = op.detalles.first()
        total_antes = self.producto.prod_cantidad_total
        services.registrar_devolucion(
            detalle=det, cantidad_devuelta=1,
            estado_devolucion=Devolucion.EstadoDevolucion.PERDIDO,
        )
        self.producto.refresh_from_db()
        # La perdida no vuelve a ningún contador; el total baja en 1
        self.assertEqual(self.producto.prod_cantidad_total, total_antes - 1)
        self.assertEqual(self.producto.prod_cantidad_prestada, 3)


class CancelarOperacionTests(TestCase):
    def setUp(self):
        self.usuario  = Usuario.objects.create_user(username="empleado", password="x")
        self.producto = crear_producto(disponible=10)
        self.client   = APIClient()
        self.client.force_authenticate(user=self.usuario)

    def test_cancelar_venta_revierte_stock(self):
        op = services.crear_operacion(
            tipo_operacion=Operacion.TipoOperacion.VENTA, usuario=self.usuario,
            detalles=[{"producto": self.producto, "cantidad": 3,
                       "precio_unitario": Decimal("100.00")}],
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
        op = services.crear_operacion(
            tipo_operacion=Operacion.TipoOperacion.PRESTAMO, usuario=self.usuario,
            detalles=[{"producto": self.producto, "cantidad": 4,
                       "precio_unitario": Decimal("0.00")}],
        )
        det = op.detalles.first()
        services.registrar_devolucion(detalle=det, cantidad_devuelta=1)

        # Cancela: solo deben volver las 3 unidades aún prestadas
        resp = self.client.post(f"/api/operaciones/operaciones/{op.id}/cancelar/")
        self.assertEqual(resp.status_code, 200)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 10)
        self.assertEqual(self.producto.prod_cantidad_prestada, 0)


class VencidosTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(username="empleado", password="x")
        self.client  = APIClient()
        self.client.force_authenticate(user=self.usuario)

    def test_lista_solo_prestamos_vencidos(self):
        hoy    = timezone.now().date()
        vencido = Operacion.objects.create(
            tipo_operacion=Operacion.TipoOperacion.PRESTAMO,
            usuario=self.usuario, fecha_devolucion=hoy - timedelta(days=1),
        )
        # Préstamo con fecha futura → NO debe aparecer
        Operacion.objects.create(
            tipo_operacion=Operacion.TipoOperacion.PRESTAMO,
            usuario=self.usuario, fecha_devolucion=hoy + timedelta(days=3),
        )

        resp = self.client.get("/api/operaciones/operaciones/vencidos/")
        self.assertEqual(resp.status_code, 200)
        codigos = [o["codigo_operacion"] for o in resp.data["results"]]
        self.assertEqual(codigos, [vencido.codigo_operacion])
