from django.test import TestCase
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.autenticacion.models import Rol, UsuarioRol

Usuario = get_user_model()


class AuthFlowTests(TestCase):
    def setUp(self):
        # Limpia el cache para no arrastrar contadores de throttling entre tests
        cache.clear()
        self.client = APIClient()
        self.usuario = Usuario.objects.create_user(
            username="empleado", password="clave-segura-123", email="e@e.com",
        )

    # ── LOGIN ────────────────────────────────
    def test_login_devuelve_tokens(self):
        resp = self.client.post("/api/auth/login/", {
            "username": "empleado", "password": "clave-segura-123",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertEqual(resp.data["user"]["username"], "empleado")

    def test_login_credenciales_invalidas(self):
        resp = self.client.post("/api/auth/login/", {
            "username": "empleado", "password": "incorrecta",
        }, format="json")
        self.assertEqual(resp.status_code, 401)

    # ── /me/ ─────────────────────────────────
    def test_me_sin_token_es_401(self):
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, 401)

    def test_me_con_token_devuelve_usuario(self):
        self.client.force_authenticate(user=self.usuario)
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["user"]["username"], "empleado")

    # ── LOGOUT (blacklist) ───────────────────
    def test_logout_invalida_el_refresh(self):
        # 1) Login para obtener el refresh
        login = self.client.post("/api/auth/login/", {
            "username": "empleado", "password": "clave-segura-123",
        }, format="json")
        refresh = login.data["refresh"]

        # 2) El refresh sirve para renovar (antes del logout)
        antes = self.client.post("/api/auth/token/refresh/",
                                 {"refresh": refresh}, format="json")
        self.assertEqual(antes.status_code, 200)

        # 3) Logout → invalida ese refresh
        logout = self.client.post("/api/auth/logout/",
                                  {"refresh": refresh}, format="json")
        self.assertEqual(logout.status_code, 200)

        # 4) Ahora el refresh YA NO sirve
        despues = self.client.post("/api/auth/token/refresh/",
                                   {"refresh": refresh}, format="json")
        self.assertEqual(despues.status_code, 401)

    def test_logout_sin_refresh_es_400(self):
        resp = self.client.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(resp.status_code, 400)

    # ── REGISTRO ─────────────────────────────
    def test_register_crea_usuario_con_rol_usuario(self):
        resp = self.client.post("/api/auth/register/", {
            "username": "nuevo", "password": "otra-clave-123",
            "email": "n@n.com", "first_name": "Ana", "last_name": "Gómez",
        }, format="json")
        self.assertIn(resp.status_code, (200, 201))
        self.assertIn("access", resp.data)
        # El usuario existe y quedó con rol 'Usuario'
        nuevo = Usuario.objects.get(username="nuevo")
        roles = UsuarioRol.objects.filter(usuario=nuevo).values_list("rol__nombre", flat=True)
        self.assertIn("Usuario", roles)
