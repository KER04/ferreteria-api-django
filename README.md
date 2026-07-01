# FERRETERIA — API de Gestión de Ferretería

API REST construida con **Django** y **Django REST Framework** para la gestión interna de una ferretería: control de inventario, venta y préstamo de productos, devoluciones y mantenimiento de unidades dañadas. Incluye autenticación por **JWT en cookies HttpOnly** y control de acceso por roles.

---

## 📋 Tabla de contenidos

- [Características](#-características)
- [Stack tecnológico](#-stack-tecnológico)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Ejecución](#-ejecución)
- [Módulos y endpoints](#-módulos-y-endpoints)
- [Autenticación](#-autenticación)
- [Permisos y roles](#-permisos-y-roles)
- [Lógica de inventario](#-lógica-de-inventario)

---

## ✨ Características

- **Inventario** con productos, categorías, marcas, fotos y código auto-generado (`CAT-MAR-001`).
- **Operaciones** de venta y préstamo con códigos auto-generados (`VEN-0001`, `PRE-0001`).
- **Devoluciones parciales y múltiples** sobre un mismo préstamo.
- **Mantenimiento** de unidades dañadas con seguimiento de recuperadas y dadas de baja.
- **Stock segmentado** (disponible / prestado / en mantenimiento / total) actualizado de forma **atómica** con `select_for_update()`.
- **Autenticación JWT** vía cookies HttpOnly + endpoint de refresh.
- **Control de acceso por roles** (administrador vs. usuario).

---

## 🛠 Stack tecnológico

| Componente | Versión |
|------------|---------|
| Python | 3.13 |
| Django | 5.2.6 |
| Django REST Framework | 3.16.1 |
| SimpleJWT | 5.5.1 |
| django-cors-headers | 4.9.0 |
| Pillow | 12.2.0 |
| Base de datos | SQLite (desarrollo) |

---

## 📁 Estructura del proyecto

```
ferreteria-api-django/
├── manage.py
├── requirements.txt
├── .env.example
├── mi_proyecto/              # Configuración del proyecto
│   ├── settings.py
│   ├── urls.py               # URLs raíz + media en desarrollo
│   └── wsgi.py / asgi.py
└── apps/
    ├── autenticacion/        # Usuarios, roles, recursos, permisos, JWT
    ├── inventario/           # Productos, categorías, marcas, préstamos
    ├── operaciones/          # Ventas, préstamos, devoluciones
    └── mantenimiento/        # Costos, tipos, registros, salidas
```

Cada app contiene sus propios `models.py`, `serializers.py`, `views.py` y `urls.py`.

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/KER04/ferreteria-api-django.git
cd ferreteria-api-django
```

### 2. Crear y activar el entorno virtual

```bash
python -m venv venv
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## ⚙ Configuración

Las variables sensibles se leen desde variables de entorno. Copia el archivo de ejemplo y ajústalo:

```bash
cp .env.example .env
```

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `SECRET_KEY` | Clave secreta de Django | clave de desarrollo (inseguro en producción) |
| `DEBUG` | Modo depuración | `True` |

> ⚠️ **Producción:** define una `SECRET_KEY` real, pon `DEBUG=False`, configura `ALLOWED_HOSTS` y cambia SQLite por PostgreSQL.

El `.env` está excluido del repositorio mediante `.gitignore`.

---

## ▶ Ejecución

```bash
# Aplicar migraciones
python manage.py migrate

# Crear un superusuario (acceso al panel /admin)
python manage.py createsuperuser

# Levantar el servidor de desarrollo
python manage.py runserver
```

La API queda disponible en `http://localhost:8000/`.

---

## 📖 Documentación interactiva de la API

Con el servidor corriendo:

| Ruta | Descripción |
|------|-------------|
| `http://localhost:8000/api/docs/` | **Swagger UI** — explora y prueba todos los endpoints |
| `http://localhost:8000/api/redoc/` | Redoc — vista alternativa de la documentación |
| `http://localhost:8000/api/schema/` | Esquema OpenAPI 3 en crudo (YAML) |

> Para probar endpoints protegidos desde Swagger: haz login en `/api/auth/login/`, copia el `access` y pégalo en el botón **Authorize** con el formato `Bearer <token>`.

## 🔌 Módulos y endpoints

> El CORS está configurado para un frontend en `http://localhost:4200` (Angular).

### Autenticación — `/api/auth/`

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/auth/register/` | Registro de usuario (devuelve tokens) |
| `POST` | `/api/auth/login/` | Login (setea cookies HttpOnly) |
| `POST` | `/api/auth/logout/` | Cierra sesión (borra cookies) |
| `GET`  | `/api/auth/hello/` | Verifica la sesión activa |
| `POST` | `/api/auth/token/refresh/` | Renueva el access token |
| `GET/POST` | `/api/auth/roles/` | Roles (admin) |
| `GET/POST` | `/api/auth/recursos/` | Recursos (admin) |

### Usuarios

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/usuarios/` | Lista de usuarios (admin) |
| `GET/PUT/DELETE` | `/usuarios/<id>/` | Detalle de usuario (admin) |

### Inventario — `/api/inventario/`

| Ruta | Recurso |
|------|---------|
| `/api/inventario/productos/` | Productos |
| `/api/inventario/tipo-categoria/` | Categorías |
| `/api/inventario/marcas/` | Marcas |
| `/api/inventario/prestamos/` | Tipos de préstamo |

Filtros de productos: `?marca=`, `?tipo_categoria=`, `?prod_estado=`. Búsqueda: `?search=`.

### Operaciones — `/api/operaciones/`

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET/POST` | `/api/operaciones/operaciones/` | Ventas y préstamos |
| `GET` | `/api/operaciones/operaciones/<id>/detalles/` | Detalles de una operación |
| `POST` | `/api/operaciones/operaciones/<id>/cancelar/` | Cancela y revierte stock |
| `POST` | `/api/operaciones/operaciones/<id>/finalizar/` | Finaliza la operación |
| `GET/POST` | `/api/operaciones/devoluciones/` | Devoluciones (solo préstamos) |

Filtros: `?tipo_operacion=`, `?estado=`, `?fecha_desde=`, `?fecha_hasta=`.

### Mantenimiento — `/api/mantenimiento/`

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET/POST` | `/api/mantenimiento/registros/` | Ingresos a mantenimiento |
| `POST` | `/api/mantenimiento/registros/<id>/finalizar/` | Registra salida y devuelve stock |
| `GET` | `/api/mantenimiento/salidas/` | Salidas (solo lectura) |
| `/api/mantenimiento/costos/` | Costos |
| `/api/mantenimiento/tipos/` | Tipos de mantenimiento |

---

## 🔐 Autenticación

El sistema usa **JWT almacenados en cookies HttpOnly** (no accesibles desde JavaScript, protección contra XSS):

- `access_token` — vida útil de 60 minutos.
- `refresh_token` — vida útil de 1 día.

Al hacer `POST /api/auth/login/` se setean ambas cookies automáticamente. El frontend debe enviar las peticiones con `credentials: 'include'`.

---

## 👥 Permisos y roles

| Permiso | Comportamiento |
|---------|----------------|
| `IsAuthenticated` | Requiere sesión activa |
| `IsAdminRole` | Solo usuarios con rol `administrador` / `admin` |
| `IsAdminOrReadOnly` | Lectura para cualquier autenticado; escritura solo admin |

**Aplicación actual:**
- **Inventario** (productos, categorías, marcas, préstamos) → cualquiera lee, solo **admin** modifica.
- **Mantenimiento** (catálogos de costos/tipos) → solo **admin** modifica.
- **Operaciones** y registro de mantenimiento → cualquier usuario autenticado (trabajo operativo diario).
- El `usuario` de cada operación/mantenimiento se toma del token, **no del cliente**, para garantizar la trazabilidad.

---

## 📦 Lógica de inventario

Cada producto mantiene su stock segmentado en cuatro cantidades:

```
prod_cantidad_total = disponible + prestada + en_mantenimiento
```

Todos los ajustes de stock ocurren dentro de **transacciones atómicas** con bloqueo de fila (`select_for_update()`) para evitar condiciones de carrera:

| Operación | Efecto en el stock |
|-----------|--------------------|
| **Venta** | `disponible −= cantidad` |
| **Préstamo** | `disponible −= cantidad`, `prestada += cantidad` |
| **Devolución** | `disponible += cantidad`, `prestada −= cantidad` |
| **Cancelar operación** | revierte el stock no devuelto |
| **Entrada a mantenimiento** | `disponible −= cantidad`, `en_mantenimiento += cantidad` |
| **Salida de mantenimiento** | recuperadas → `disponible`; bajas → se descuentan |

El **estado** del producto (`Disponible`, `Prestado`, `Mantenimiento`, `Dañado`, `Agotado`) se calcula automáticamente al guardar.

---

## 📝 Pendientes / Roadmap

- [x] Tests automatizados de la lógica de stock
- [x] Alerta de stock bajo (`?bajo_stock=true`)
- [x] Endpoint de dashboard (`/api/inventario/dashboard/`)
- [x] Documentación interactiva (Swagger / drf-spectacular)
- [x] Configuración de logging
- [x] Rate-limiting (throttling) en autenticación
- [x] Base de datos configurable vía `DATABASE_URL`
- [ ] Migración real a PostgreSQL para producción
- [ ] Docker + CI/CD
- [ ] Almacenamiento de archivos en la nube (S3) para `media/`
- [ ] Permisos granulares por recurso (`TieneAccesoRecurso`)

---

> Proyecto **Ferretería** — versión preliminar.
