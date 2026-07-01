# Importaciones:
from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, inline_serializer
from django.contrib.auth import authenticate
from .models import Usuario, Rol, UsuarioRol, Recurso, RecursoRol
from .permissions import TieneAccesoRecurso, IsAdminRole
from .serializers import (
    RegisterSerializer, UsuarioSerializer, RolSerializer,
    UsuarioRolSerializer, RecursoSerializer, RecursoRolSerializer,
)

# REGISTRO DE USUARIOS
# NOTA: hoy es público. Para un sistema interno, considera cambiar a
# [IsAuthenticated, IsAdminRole] para que solo un admin cree empleados.
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    queryset = Usuario.objects.all()
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # 'user' es la instancia de Usuario

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nombres': user.first_name,
                'apellidos': user.last_name,
            }
        })

# VISTAS DE USUARIOS
class UsuarioListView(generics.ListAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

class UsuarioRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

# INICIAR SESION — devuelve los tokens en el body (auth por header Bearer)
@extend_schema(
    request=inline_serializer("LoginRequest", {
        "username": drf_serializers.CharField(),
        "password": drf_serializers.CharField(),
    }),
    responses=inline_serializer("LoginResponse", {
        "access":  drf_serializers.CharField(),
        "refresh": drf_serializers.CharField(),
        "user":    drf_serializers.DictField(),
    }),
    summary="Iniciar sesión",
)
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        })

# VERIFICACION DE AUTENTICACION — usuario del token actual
@extend_schema(
    responses=inline_serializer("MeResponse", {
        "user": drf_serializers.DictField(),
    }),
    summary="Usuario autenticado actual",
)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        })

# CERRAR SESION
# Con auth por header Bearer, el cierre de sesión es del lado del cliente:
# el frontend descarta el access token. (El refresh expira solo en 1 día.)
# Si en el futuro quieres invalidar tokens en servidor, habilita la app
# token_blacklist de SimpleJWT y haz blacklist del refresh aquí.
@extend_schema(
    request=None,
    responses=inline_serializer("LogoutResponse", {
        "message": drf_serializers.CharField(),
    }),
    summary="Cerrar sesión (lado cliente)",
)
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"message": "Sesión cerrada. Descarta el token en el cliente."})
    
# ROLES
class RolListCreateView(generics.ListCreateAPIView):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

class RolRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

class UsuarioRolCreateView(generics.CreateAPIView):
    queryset = UsuarioRol.objects.all()
    serializer_class = UsuarioRolSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

# Listar y crear recursos
class RecursoListCreateView(generics.ListCreateAPIView):
    queryset = Recurso.objects.all()
    serializer_class = RecursoSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

# Ver, actualizar o eliminar un recurso
class RecursoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Recurso.objects.all()
    serializer_class = RecursoSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

# Asignar recursos a roles
class RecursoRolCreateView(generics.CreateAPIView):
    queryset = RecursoRol.objects.all()
    serializer_class = RecursoRolSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

# Listar todos los recursos por rol
class RecursosPorRolListView(generics.ListAPIView):
    """
    - GET /api/autenticacion/recursos-rol/           -> todas las asignaciones recurso–rol
    - GET /api/autenticacion/recursos-rol/<rol_id>/  -> asignaciones del rol indicado
    """
    serializer_class = RecursoRolSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        rol_id = self.kwargs.get('rol_id')
        qs = RecursoRol.objects.select_related('rol', 'recurso').all()
        if rol_id is not None:
            qs = qs.filter(rol_id=rol_id)
        return qs