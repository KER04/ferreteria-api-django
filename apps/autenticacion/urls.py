from django.urls import path
from .views import *

urlpatterns = [
    path('hello/', HelloFromCookieView.as_view(), name='hello'),
    
    path('login/', CookieLoginView.as_view(), name='login_cookie'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('roles/', RolListCreateView.as_view(), name='rol_list_create'),
    path('roles/crear/', RolListCreateView.as_view(), name='rol_list_create'),
    path('roles/<int:pk>/', RolRetrieveUpdateDestroyView.as_view(), name='rol_detail'),
    path('roles/asignar-rol/', UsuarioRolCreateView.as_view(), name='usuario_rol_create'),

    path('recursos/', RecursoListCreateView.as_view(), name='lista-crea-recursos'),
    path('recursos/<int:pk>/', RecursoRetrieveUpdateDestroyView.as_view(), name='ver-editar-eliminar-recurso'),
    path('recursos-rol/', RecursoRolCreateView.as_view(), name='asignar-recurso-a-rol'),
    path('recursos-rol-list/', RecursosPorRolListView.as_view(), name='recursos-rol-list'),
    path('recursos-rol/<int:rol_id>/', RecursosPorRolListView.as_view(), name='recursos-por-rol'),
]
