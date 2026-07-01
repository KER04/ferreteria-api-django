from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.inventario.models import Marca, Prestamo, Producto, TipoCategoria
from apps.mantenimiento import services
from apps.mantenimiento.models import (
    Mantenimiento,
    SalidaMantenimiento,
    TipoMantenimiento,
)

Usuario = get_user_model()


def crear_producto(disponible=10):
    categoria = TipoCategoria.objects.create(tipr_nombre="Herramientas")
    marca     = Marca.objects.create(marca_nombre="Truper")
    prestamo  = Prestamo.objects.create(pres_nombre="Estándar", tipo_prestamo="interno")
    return Producto.objects.create(
        prod_nombre="Taladro",
        prod_valor_unitario=Decimal("100.00"),
        prod_cantidad_disponible=disponible,
        tipo_categoria=categoria,
        marca=marca,
        prestamo=prestamo,
    )


class MantenimientoStockTests(TestCase):
    def setUp(self):
        self.usuario  = Usuario.objects.create_user(username="tecnico", password="x")
        self.producto = crear_producto(disponible=10)
        self.tipo     = TipoMantenimiento.objects.create(tima_nombre="Correctivo")

    def _ingresar(self, cantidad):
        return services.ingresar_mantenimiento(
            producto=self.producto,
            tipo_mantenimiento=self.tipo,
            cantidad_ingresada=cantidad,
            usuario=self.usuario,
        )

    def test_ingreso_descuenta_disponible(self):
        self._ingresar(3)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 7)
        self.assertEqual(self.producto.prod_cantidad_en_mantenimiento, 3)

    def test_salida_recupera_y_da_de_baja(self):
        mant = self._ingresar(3)
        services.registrar_salida(
            mantenimiento=mant, cantidad_recuperada=2, cantidad_baja=1,
        )
        self.producto.refresh_from_db()
        mant.refresh_from_db()
        # 2 vuelven al stock, 1 se pierde; 3 salen de mantenimiento
        self.assertEqual(self.producto.prod_cantidad_disponible, 9)
        self.assertEqual(self.producto.prod_cantidad_en_mantenimiento, 0)
        self.assertEqual(mant.estado, Mantenimiento.Estado.FINALIZADO)


class CancelarMantenimientoTests(TestCase):
    def setUp(self):
        self.usuario  = Usuario.objects.create_user(username="tecnico", password="x")
        self.producto = crear_producto(disponible=10)
        self.tipo     = TipoMantenimiento.objects.create(tima_nombre="Correctivo")
        self.client   = APIClient()
        self.client.force_authenticate(user=self.usuario)

    def test_cancelar_devuelve_stock(self):
        mant = services.ingresar_mantenimiento(
            producto=self.producto,
            tipo_mantenimiento=self.tipo,
            cantidad_ingresada=4,
            usuario=self.usuario,
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.prod_cantidad_disponible, 6)
        self.assertEqual(self.producto.prod_cantidad_en_mantenimiento, 4)

        resp = self.client.post(f"/api/mantenimiento/registros/{mant.pk}/cancelar/")
        self.assertEqual(resp.status_code, 200)

        mant.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertEqual(mant.estado, Mantenimiento.Estado.CANCELADO)
        self.assertEqual(self.producto.prod_cantidad_disponible, 10)
        self.assertEqual(self.producto.prod_cantidad_en_mantenimiento, 0)
