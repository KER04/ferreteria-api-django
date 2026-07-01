from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.autenticacion.models import Rol, UsuarioRol
from apps.inventario.models import Marca, Prestamo, Producto, TipoCategoria

Usuario = get_user_model()


def crear_usuario(username, admin=False):
    user = Usuario.objects.create_user(username=username, password="x")
    if admin:
        rol = Rol.objects.create(nombre="Administrador")
        UsuarioRol.objects.create(usuario=user, rol=rol)
    return user


class PermisosInventarioTests(TestCase):
    """Verifica IsAdminOrReadOnly y el default-deny."""

    def setUp(self):
        self.categoria = TipoCategoria.objects.create(tipr_nombre="Herramientas")
        self.marca     = Marca.objects.create(marca_nombre="Truper")
        self.prestamo  = Prestamo.objects.create(pres_nombre="Estándar", tipo_prestamo="interno")
        self.admin     = crear_usuario("admin", admin=True)
        self.normal    = crear_usuario("normal", admin=False)
        self.client    = APIClient()

    def _payload(self):
        return {
            "prod_nombre": "Martillo",
            "prod_valor_unitario": "50.00",
            "prod_cantidad_disponible": 5,
            "tipo_categoria": self.categoria.pk,
            "marca": self.marca.pk,
            "prestamo": self.prestamo.pk,
        }

    # ── default-deny ─────────────────────────
    def test_sin_autenticar_no_lista_productos(self):
        resp = self.client.get("/api/inventario/productos/")
        self.assertEqual(resp.status_code, 401)

    # ── lectura permitida a cualquier autenticado ──
    def test_usuario_normal_puede_leer(self):
        self.client.force_authenticate(user=self.normal)
        resp = self.client.get("/api/inventario/productos/")
        self.assertEqual(resp.status_code, 200)

    # ── escritura solo admin ─────────────────
    def test_usuario_normal_no_puede_crear(self):
        self.client.force_authenticate(user=self.normal)
        resp = self.client.post("/api/inventario/productos/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 403)

    def test_admin_puede_crear(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post("/api/inventario/productos/", self._payload(), format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Producto.objects.filter(prod_nombre="Martillo").exists())


class DashboardTests(TestCase):
    def setUp(self):
        self.categoria = TipoCategoria.objects.create(tipr_nombre="Herramientas")
        self.marca     = Marca.objects.create(marca_nombre="Truper")
        self.prestamo  = Prestamo.objects.create(pres_nombre="Estándar", tipo_prestamo="interno")
        Producto.objects.create(
            prod_nombre="Taladro", prod_valor_unitario=Decimal("100.00"),
            prod_cantidad_disponible=3, tipo_categoria=self.categoria,
            marca=self.marca, prestamo=self.prestamo,
        )
        self.user   = Usuario.objects.create_user(username="u", password="x")
        self.client = APIClient()

    def test_dashboard_requiere_autenticacion(self):
        resp = self.client.get("/api/inventario/dashboard/")
        self.assertEqual(resp.status_code, 401)

    def test_dashboard_devuelve_resumen(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/inventario/dashboard/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("inventario", resp.data)
        self.assertIn("operaciones", resp.data)
        self.assertEqual(resp.data["inventario"]["total_productos"], 1)
