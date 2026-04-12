# Importaciones: 
from rest_framework import generics, permissions, status
from .models import Usuario
from serializer.serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from apps.autenticacion.permissions import TieneAccesoRecurso, IsAdminRole

# REGISTRO DE USUARIOS
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    queryset = Usuario.objects.all()

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

# INICIAR SESION
class CookieLoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            "message": "Autenticación con cookies exitosa",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        })

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,          # en prod; en local usa HTTPS o, si no puedes, pon False temporalmente
            samesite='None',      # <— clave para cross-origin
            max_age=60*60,
        )

        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=True,          # idem
            samesite='None',
            max_age=60*60*24,
        )

        return response

# VERIFICACION DE AUTENTICACION
class HelloFromCookieView(APIView):
    def get(self, request):
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return Response({"detail": "No se encontró el token en cookies"}, status=401)
        
        jwt_authenticator = JWTAuthentication()
        try:
            validated_user, token = jwt_authenticator.authenticate(request._request)
        except Exception as e:
            return Response({"detail": f"Token inválido: {str(e)}"}, status=401)

        return Response({
            "message": f"Hola, {validated_user.username}, estas autenticado <3"
        })

# CERRAR SESION
class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Sesión cerrada correctamente."})
        
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        
        return response
    
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