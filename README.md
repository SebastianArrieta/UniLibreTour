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
│   ├── __init__.py             # Factory create_app: config, blueprints, catálogo base
│   ├── config.py               # Configuración dev/prod/test, cookies y correo
│   ├── extensions.py           # db, jwt y validaciones de tokens
│   ├── controllers/
│   │   ├── auth.py             # Login, /me, logout, 2FA
│   │   ├── usuarios.py         # CRUD /api/usuarios (con roles)
│   │   ├── admin.py            # Altas y validación /api/admin
│   │   ├── notificaciones.py   # Notificaciones del usuario
│   │   ├── museo.py            # Lectura del dataset + aportes
│   │   ├── web.py              # Vistas HTML y guardas por rol
│   │   └── health.py           # GET /api/health
│   ├── middleware/auth.py      # role_required y web_role_required
│   ├── models/                 # Modelos SQLAlchemy (usuario, contenido, …)
│   ├── schemas/                # Schemas de validación Marshmallow
│   ├── services/
│   │   ├── auth.py             # Hash/verificación de contraseñas
│   │   ├── usuario.py          # CRUD de usuarios
│   │   ├── catalogo.py         # Colecciones/insignias base + primer admin (ADMIN_*)
│   │   ├── otp.py              # Códigos 2FA (HMAC, sin estado)
│   │   ├── correo.py           # Envío SMTP del código 2FA
│   │   ├── limite.py           # Límite de intentos en login/2FA
│   │   ├── museo.py            # Lectura del museo desde la BD
│   │   ├── admin.py            # Altas directas y validación
│   │   ├── notificacion.py     # Avisos al usuario
│   │   └── contenido.py        # Reglas de aportes
│   ├── static/
│   │   ├── css/main.css
│   │   ├── js/utils/{api,app,ui}.js
│   │   ├── js/pages/usuarios.js
│   │   └── images/             # Escudo y marcadores de imagen locales
│   └── templates/
│       ├── base.html
│       ├── auth/               # login, 2fa
│       ├── publico/            # home, explorar, cronología, perfil, …
│       ├── estudiante/         # dashboard, aportes, favoritos, contribuir
│       ├── docente/            # dashboard, evidencia, notificaciones
│       ├── admin/              # dashboard, cola, usuarios, registros, …
│       └── components/         # header, footer, sidebar, logo, macros
├── database/init/01_schema.sql # Esquema de referencia
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── run.py                      # Punto de entrada
```

> El esquema lo crea **SQLAlchemy** (`db.create_all()`) al iniciar. El SQL de
> `database/init/` es documentación/referencia.

## Puesta en marcha desde cero

La aplicación arranca **vacía**: no hay datos ni cuentas de demostración. Al
iniciar solo se crean el catálogo base (6 colecciones temáticas y 12 insignias)
y, si no existe ninguno, el **primer administrador** definido en el `.env`.
Todo lo demás (usuarios, aportes, noticias, eventos, hitos, premios, Hall de la
Fama, semilleros) se registra desde la propia aplicación.

### Opción A — Docker (recomendada)

```bash
cp .env.example .env
# Completa SECRET_KEY, JWT_SECRET_KEY, MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD,
# ADMIN_EMAIL y ADMIN_PASSWORD (y MAIL_* si usarás 2FA).
docker compose up --build -d
```

1. Entra en <http://localhost:5000/login> con `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
2. En **Panel Admin → Usuarios** crea las cuentas de docentes, estudiantes y egresados.
3. En **Panel Admin → Añadir información** publica noticias, eventos, hitos, premios, Hall de la Fama y semilleros.
4. Los estudiantes aportan contenido → revisión docente → validación del admin → publicado.

- Health check (incluye la BD): <http://localhost:5000/api/health>
- La BD no publica puertos fuera de Docker.
- `JWT_COOKIE_SECURE=1` exige HTTPS (pon la app detrás de un proxy con TLS). Para
  probar por HTTP en tu máquina usa `JWT_COOKIE_SECURE=0`.

> **¿Vienes de una versión con datos demo?** El volumen de MySQL conserva lo
> sembrado antes. Para empezar en blanco hay que borrarlo (destruye todos los
> datos): `docker compose down -v` y luego `docker compose up --build -d`.

### Opción B — Local (desarrollo)

Requisitos: Python 3.12+ y MySQL 8.0.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
# En .env: FLASK_ENV=development, DATABASE_URL=..., ADMIN_EMAIL, ADMIN_PASSWORD
python run.py
```

## Variables de entorno

| Variable | Descripción | Por defecto |
|---|---|---|
| `FLASK_ENV` | `development` / `production` / `testing` | `production` en Docker |
| `SECRET_KEY` | Clave de sesión de Flask (**obligatoria en producción**) | — |
| `JWT_SECRET_KEY` | Clave de firma de los JWT (**obligatoria en producción**) | — |
| `DATABASE_URL` | URI de conexión SQLAlchemy (Docker la arma con `MYSQL_*`) | MySQL local |
| `JWT_COOKIE_SECURE` | `1` cookie solo por HTTPS | `1` en producción |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Primer administrador (solo si no hay ninguno; si el email ya existe, esa cuenta pasa a admin con esta contraseña) | — |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_FROM`, `MAIL_USE_TLS`, `MAIL_USE_SSL` | SMTP para enviar el código 2FA | sin correo |
| `OTP_DEV_ECHO` | Solo desarrollo: muestra el código 2FA en pantalla | `0` |

> En producción la app **no arranca** si `SECRET_KEY` o `JWT_SECRET_KEY` faltan
> o tienen un valor de ejemplo. Si no hay SMTP configurado, el 2FA se omite (con
> aviso en el log) para no bloquear a nadie.

## Autenticación y seguridad

- El JWT viaja en el header `Authorization: Bearer` para la API **y** en una
  cookie **httpOnly** (`museo_session`) para proteger las vistas HTML.
- Las vistas `/admin*`, `/docente*`, `/estudiante*` y `/perfil` validan el rol
  **en el servidor** a partir del token firmado; sin sesión redirigen a
  `/login?next=…`. El rol de `localStorage` solo controla la interfaz.
- CSRF activado para peticiones que usan la cookie (el frontend usa Bearer).
- Las cuentas **solo las crea el administrador** (`/admin/usuarios`); no existe registro público.
- El 2FA envía un código de 6 dígitos por correo (SMTP) y se verifica en el
  servidor con huella HMAC y máximo 5 intentos (reenviar no reinicia el
  contador). El token de desafío no sirve como sesión.
- Login y 2FA bloquean temporalmente tras 10 intentos **fallidos** por cuenta (15 min); los accesos correctos nunca cuentan.
- Los aportes sin aprobar solo los ven su autor, docentes y administradores.

## Endpoints de la API

### Autenticación

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/api/auth/login` | Iniciar sesión (JWT + cookie) | — |
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
| GET | `/api/health` | Estado del servidor y de la BD | — |
| GET | `/api/museo/data` | Dataset público (sin cola ni emails) | — |
| GET | `/api/museo/<seccion>` | Sección (`colecciones`, `noticias`, `linea-tiempo`, `eventos`, `contenidos`, `hall`, `insignias`, `usuarios`, `grupos`, `logros`, `docentes`, `kpi`) | — |
| POST | `/api/museo/contenidos` | Registrar aporte (revisión docente o cola) | JWT |
| PUT | `/api/museo/contenidos/<id>/docente-revision` | Docente aprueba/devuelve aporte | docente/admin |
| GET | `/api/museo/contenidos/<id>/comentarios` | Comentarios de una pieza | — |
| POST | `/api/museo/contenidos/<id>/comentarios` | Publicar comentario | JWT |
| DELETE | `/api/museo/comentarios/<id>` | Eliminar comentario (autor/admin) | JWT |
| GET | `/api/museo/favoritos` | Ids favoritos del usuario | JWT |
| POST | `/api/museo/favoritos/<id>` | Alternar favorito | JWT |
| DELETE | `/api/museo/favoritos[/<id>]` | Quitar uno o todos | JWT |

### Administración

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| POST | `/api/admin/hitos` | Crear hito de cronología | admin |
| POST | `/api/admin/premios` | Crear premio/logro | admin |
| POST | `/api/admin/proyectos` | Crear proyecto | admin |
| POST | `/api/admin/hall` | Crear miembro del Hall de la Fama | admin |
| POST | `/api/admin/eventos` | Crear evento | admin |
| POST | `/api/admin/noticias` | Crear noticia | admin |
| POST | `/api/admin/semilleros` | Crear semillero o grupo de investigación | admin |
| PUT | `/api/admin/contenidos/<id>/validar` | Aprobar o devolver contenido | admin |
| PUT | `/api/admin/usuarios/<id>` | Editar usuario | admin |
| PUT | `/api/admin/usuarios/<id>/aprobar` | Aprobar cuenta pendiente | admin |

### Notificaciones

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/api/notificaciones` | Notificaciones del usuario | JWT |
| PUT | `/api/notificaciones/leidas` | Marcar todas como leídas | JWT |
| PUT | `/api/notificaciones/<id>` | Marcar una notificación | JWT |

### Vistas HTML

| Ruta | Acceso |
|---|---|
| `/`, `/explorar`, `/buscar`, `/detalle/<id>`, `/hall-fama`, `/semilleros`, `/calendario`, `/cronologia`, `/ranking`, `/login`, `/2fa` | Público |
| `/egresado` | `egresado` o `admin` |
| `/perfil` | Autenticado |
| `/estudiante`, `/estudiante/aportes`, `/estudiante/contribuir` | `estudiante` o `admin` |
| `/estudiante/favoritos` | autenticado |
| `/docente`, `/docente/revision`, `/docente/registrar-evidencia`, `/docente/notificaciones` | `docente` o `admin` |
| `/admin`, `/admin/anadir`, `/admin/usuarios`, `/admin/cola`, `/admin/validacion/<id>`, `/admin/confirmacion/<id>`, `/admin/registros`, `/admin/hall-registro` | `admin` |

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
  -d '{"email": "<ADMIN_EMAIL>", "password": "<ADMIN_PASSWORD>"}'
```
