# 🏛️ UniLibreTour

Plataforma interactiva del **museo digital universitario** del Programa de
Ingeniería de Sistemas — Universidad Libre. Aplicación monolítica **Flask**
(patrón MVC) con vistas **Jinja2**, API REST y autenticación **JWT**.

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12+ / Flask 3.1 |
| ORM | Flask-SQLAlchemy 3.1 (SQLAlchemy 2.x) |
| Base de datos | MySQL 8.0 (SQLite válido para pruebas) |
| Validación | Marshmallow 4 |
| Autenticación | Flask-JWT-Extended 4.7 (JWT + roles + 2FA) |
| Frontend | Jinja2 + CSS + JavaScript vanilla |
| Contenedores | Docker + Docker Compose |
| Servidor WSGI | Gunicorn |

## Estructura del proyecto

```
UniLibreTour/
├── app/
│   ├── __init__.py             # Factory create_app: config, blueprints, seeds
│   ├── config.py               # Configuración dev/prod/test + cookies y seeds
│   ├── extensions.py           # db, jwt y validaciones de tokens
│   ├── controllers/
│   │   ├── auth.py             # Login, registro, /me, logout, 2FA
│   │   ├── usuarios.py         # CRUD /api/usuarios (con roles)
│   │   ├── museo.py            # Lectura del dataset + aportes
│   │   ├── web.py              # Vistas HTML y guardas por rol
│   │   ├── views.py            # Vista legada /usuarios (solo admin)
│   │   └── health.py           # GET /api/health
│   ├── middleware/auth.py      # role_required y web_role_required
│   ├── models/                 # Modelos SQLAlchemy (usuario, contenido, …)
│   ├── schemas/                # Schemas de validación Marshmallow
│   ├── services/
│   │   ├── auth.py             # Hash/verificación de contraseñas
│   │   ├── usuario.py          # CRUD de usuarios + seed de cuentas
│   │   ├── cuentas.py          # Única fuente de verdad de cuentas demo
│   │   ├── otp.py              # Códigos 2FA (HMAC, sin estado)
│   │   ├── seed_demo.py        # Dataset demo desde demo-data.json
│   │   ├── museo.py            # Lectura del museo desde la BD
│   │   └── contenido.py        # Reglas de aportes
│   ├── static/
│   │   ├── css/main.css
│   │   ├── js/utils/{api,app,ui}.js
│   │   ├── js/pages/usuarios.js
│   │   └── data/demo-data.json # Dataset de respaldo (sin credenciales)
│   └── templates/
│       ├── base.html
│       ├── auth/               # login, registro, 2fa
│       ├── publico/            # home, explorar, cronología, perfil, …
│       ├── estudiante/         # dashboard, aportes, favoritos, contribuir
│       ├── docente/            # dashboard, evidencia, notificaciones
│       ├── admin/              # dashboard, cola, usuarios, registros, …
│       └── components/         # header, footer, sidebar, logo, macros
├── database/init/01_schema.sql # Esquema de referencia
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── reset_demo.py               # Reinicia esquema y resiembra (¡dev only!)
└── run.py                      # Punto de entrada
```

> El esquema lo crea **SQLAlchemy** (`db.create_all()`) al iniciar. El SQL de
> `database/init/` es documentación/referencia.

## Instalación

### Opción A — Docker (recomendada)

```bash
cp .env.example .env
docker compose up --build
```

- App: <http://localhost:5000>
- Health check: <http://localhost:5000/api/health>

### Opción B — Local

Requisitos: Python 3.12+ y MySQL 8.0.

```bash
mysql -u root -p -e "CREATE DATABASE unilibretour_db; CREATE USER 'unilibretour'@'localhost' IDENTIFIED BY 'unilibretour'; GRANT ALL PRIVILEGES ON unilibretour_db.* TO 'unilibretour'@'localhost'; FLUSH PRIVILEGES;"

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## Variables de entorno

| Variable | Descripción | Por defecto |
|---|---|---|
| `FLASK_ENV` | `development` / `production` / `testing` | `development` |
| `SECRET_KEY` | Clave de sesión de Flask | `dev-secret` |
| `JWT_SECRET_KEY` | Clave de firma de los JWT | `dev-secret` |
| `DATABASE_URL` | URI de conexión SQLAlchemy | MySQL local |
| `JWT_COOKIE_SECURE` | `1` para cookie solo por HTTPS (producción) | `0` |
| `SEED_DEMO` | `1` siembra datos y cuentas demo | `1` (dev), `0` (prod) |
| `OTP_DEV_ECHO` | Devuelve el código 2FA en la respuesta (dev) | `1` |

> **Producción:** `JWT_COOKIE_SECURE=1`, `SEED_DEMO=0` y `OTP_DEV_ECHO=0`
> (requiere integrar un proveedor de correo para el 2FA).

## Autenticación y seguridad

- El JWT viaja en el header `Authorization: Bearer` para la API **y** en una
  cookie **httpOnly** (`museo_session`) para proteger las vistas HTML.
- Las vistas `/admin*`, `/docente*`, `/estudiante*` y `/perfil` validan el rol
  **en el servidor** a partir del token firmado; sin sesión redirigen a
  `/login?next=…`. El rol de `localStorage` solo controla la interfaz.
- CSRF activado para peticiones que usan la cookie (el frontend usa Bearer).
- El registro público crea la cuenta en estado **pendiente**: no entrega sesión
  hasta que un administrador la apruebe.
- El 2FA se verifica en el servidor con código de 6 dígitos, huella HMAC y
  máximo 5 intentos. El token de desafío no sirve como sesión.

## Endpoints de la API

### Autenticación

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/api/auth/login` | Iniciar sesión (JWT + cookie) | — |
| POST | `/api/auth/register` | Registro (queda pendiente) | — |
| GET | `/api/auth/me` | Perfil de la sesión actual | JWT |
| POST | `/api/auth/logout` | Cerrar sesión y borrar cookie | — |
| POST | `/api/auth/2fa/verify` | Verificar código 2FA | Token de desafío |
| POST | `/api/auth/2fa/resend` | Reenviar código 2FA | Token de desafío |

### Usuarios

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/api/usuarios` | Listar usuarios | admin |
| GET | `/api/usuarios/<id>` | Obtener usuario | propio o admin |
| POST | `/api/usuarios` | Crear usuario | admin |
| PUT | `/api/usuarios/<id>` | Actualizar (`nombre` propio) | propio o admin |
| DELETE | `/api/usuarios/<id>` | Eliminar usuario | admin |

### Museo

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/api/health` | Estado del servidor | — |
| GET | `/api/museo/data` | Dataset completo | — |
| GET | `/api/museo/<seccion>` | Sección (`colecciones`, `noticias`, `linea-tiempo`, `eventos`, `contenidos`, `cola`, `hall`, `insignias`, `usuarios`, `grupos`, `logros`, `docentes`, `kpi`) | — |
| POST | `/api/museo/contenidos` | Registrar aporte (queda en cola) | JWT |

### Vistas HTML

| Ruta | Acceso |
|---|---|
| `/`, `/explorar`, `/buscar`, `/detalle/<id>`, `/hall-fama`, `/semilleros`, `/calendario`, `/cronologia`, `/ranking`, `/egresado`, `/login`, `/registro`, `/2fa` | Público |
| `/perfil` | Autenticado |
| `/estudiante`, `/estudiante/aportes`, `/estudiante/favoritos`, `/estudiante/contribuir` | `estudiante` o `admin` |
| `/docente`, `/docente/registrar-evidencia`, `/docente/notificaciones` | `docente` o `admin` |
| `/admin`, `/admin/anadir`, `/admin/usuarios`, `/admin/cola`, `/admin/validacion/<id>`, `/admin/confirmacion/<id>`, `/admin/registros`, `/admin/hall-registro` | `admin` |
| `/usuarios` (vista legada) | `admin` |

### Formato de respuesta

```json
{ "ok": true,  "data": { } }
{ "ok": false, "error": "mensaje de error" }
```

En errores de validación, `error` contiene el diccionario de Marshmallow.

### Ejemplo de login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email": "admin@unilibre.edu.co", "password": "123456"}'
```

## Cuentas demo (seed)

El seed se ejecuta al arrancar **solo si `SEED_DEMO=1`** (por defecto en
desarrollo y pruebas). Es idempotente por email: crea únicamente las cuentas
que falten.

| Rol | Email | Contraseña |
|---|---|---|
| admin | `admin@unilibre.edu.co` | `123456` |
| estudiante | `estudiante@unilibre.edu.co` | `123456` |
| docente | `docente@unilibre.edu.co` | `123456` |
| egresado | `egresado@unilibre.edu.co` | `123456` |

Además se siembran los perfiles de contenido del museo (docentes, estudiantes
y egresados) que también usan la contraseña demo; sus emails siguen el patrón
`nombre.apellido@unilibre.edu.co`.

> Las credenciales demo son solo para desarrollo. En producción no se siembran
> (`SEED_DEMO=0`) y deben existir cuentas reales creadas por un administrador.

## Utilidades

```bash
# Reinicia el esquema y vuelve a sembrar el dataset demo (¡destruye datos!)
python reset_demo.py
```
