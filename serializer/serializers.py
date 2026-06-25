# Shim de compatibilidad — los serializers viven ahora en cada app.
# Este archivo re-exporta todo para no romper imports externos que aún lo usen.
from apps.autenticacion.serializers import (  # noqa: F401
    RegisterSerializer,
    UsuarioSerializer,
    LoginSerializer,
    RolSimpleSerializer,
    RolSerializer,
    UsuarioRolSerializer,
    RecursoSerializer,
    RecursoRolSerializer,
)
from apps.inventario.serializers import (  # noqa: F401
    TipoCategoriaSerializer,
    MarcaSerializer,
    PrestamoSerializer,
    ProductoSerializer,
    ProductoReadSerializer,
)
