from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# Se lee de .env (o variable de entorno). El default solo aplica en desarrollo.
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-m3sfi(p577hkwgu9q1-fuxudanrm9gn=)pefk0ifqb$ho+41ck',
)

# SECURITY WARNING: don't run with debug turned on in production!
# Define DEBUG=False en el .env del servidor de producción.
DEBUG = config('DEBUG', default=True, cast=bool)

# Hosts permitidos: en producción define ALLOWED_HOSTS=midominio.com,www.midominio.com
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.inventario.apps.InventarioConfig',
    'apps.mantenimiento.apps.MantenimientoConfig',
    'apps.operaciones.apps.OperacionesConfig',

    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',

    'apps.autenticacion',
    # CORS
    'corsheaders',

]

MIDDLEWARE = [
    # CORS debe ir lo más arriba posible
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mi_proyecto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mi_proyecto.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Configurable por entorno. En desarrollo cae a SQLite; en producción define
# DATABASE_URL=postgres://usuario:password@host:5432/nombre_db en el .env.
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600,
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

#JWT

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Denegar por defecto: todo endpoint exige autenticación salvo que
    # declare explícitamente AllowAny (login, registro, logout).
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Genera el esquema OpenAPI para Swagger/Redoc
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Límite de peticiones — protege contra abuso y fuerza bruta
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': config('THROTTLE_ANON', default='100/hour'),
        'user': config('THROTTLE_USER', default='1000/hour'),
        'auth': config('THROTTLE_AUTH', default='10/min'),  # login / registro
    },
    # Convierte errores de validación de modelo (django) en 400 uniformes
    'EXCEPTION_HANDLER': 'mi_proyecto.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ─────────────────────────────────────────────────────────────────
# OpenAPI / Swagger (drf-spectacular)
# ─────────────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'API Ferretería',
    'DESCRIPTION': (
        'API REST para gestión de inventario, ventas, préstamos, '
        'devoluciones y mantenimiento de una ferretería. '
        'Autenticación por JWT (header Authorization: Bearer <token>).'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,      # no exponer el schema crudo en /docs
    'COMPONENT_SPLIT_REQUEST': True,    # separa serializers de lectura/escritura
}

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# ─── Media files (imágenes de productos, etc.) ───────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Las imágenes de productos se guardan en:
#   <BASE_DIR>/media/productos/fotos/<filename>
# Y se acceden en desarrollo desde:
#   http://localhost:8000/media/productos/fotos/<filename>

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'autenticacion.Usuario'


# Orígenes del frontend. En producción define en .env:
#   CORS_ALLOWED_ORIGINS=https://miferreteria.com,https://www.miferreteria.com
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:4200',
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True # Permite enviar cookies (como el token JWT) en solicitudes CORS

# Orígenes confiables para CSRF (normalmente los mismos que CORS).
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:4200',
    cast=Csv(),
)


# ─────────────────────────────────────────────────────────────────
# LOGGING — salida estructurada a consola (stdout)
# En producción, el orquestador (Docker/systemd) recoge stdout.
# ─────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        # Errores 500 y excepciones no controladas
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


