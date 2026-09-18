# 🏛️ UniLibreTour

Plataforma interactiva para la gestión y exploración de exposiciones del **museo digital universitario**. Aplicación monolítica construida con **Flask** siguiendo el patrón **MVC**, con vistas renderizadas en **Jinja2** y una API REST con autenticación **JWT**.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12 / Flask 3.1 |
| ORM | Flask-SQLAlchemy 3.1 (SQLAlchemy 2.x) |
| Base de datos | MySQL 8.0 |
| Validación | Marshmallow 4 |
| Autenticación | Flask-JWT-Extended (JWT con roles) |
| Frontend | Jinja2 + CSS + JavaScript vanilla |
| Contenedores | Docker + Docker Compose |
| Servidor WSGI | Gunicorn |

## Estructura del Proyecto

```
UniLibreTour/
├── app/
│   ├── __init__.py          # Factory create_app: blueprints, db, seed
│   ├── config.py            # Configuración por entorno (dev/prod/test)
│   ├── extensions.py        # Instancias compartidas (db, jwt)
│   ├── controllers/         # Capa de presentación (blueprints Flask)
│   │   ├── auth.py          #   POST /api/auth/login
│   │   ├── health.py        #   GET  /api/health
│   │   ├── usuarios.py      #   CRUD /api/usuarios
│   │   └── views.py         #   Páginas Jinja2 (/, /usuarios)
│   ├── models/              # Modelos SQLAlchemy
│   │   └── usuario.py       #   Tabla `usuarios`
│   ├── schemas/             # Schemas Marshmallow (validación/serialización)
│   │   ├── auth.py
│   │   └── usuario.py
│   ├── services/            # Lógica de negocio (incluye seeds de usuarios)
│   │   ├── auth.py
│   │   └── usuario.py
│   ├── middleware/          # Decoradores de autorización
│   │   └── auth.py          #   role_required(*roles)
│   ├── utils/               # Utilidades
│   │   └── response.py      #   json_ok / json_error (formato {ok, data, error})
│   ├── static/
│   │   ├── css/main.css
│   │   ├── js/pages/usuarios.js
│   │   ├── fonts/
│   │   └── images/
│   └── templates/           # Plantillas Jinja2
│       ├── base.html
│       ├── index.html
│       ├── usuarios.html
│       └── components/navbar.html
├── database/
│   └── init/01_schema.sql   # Esquema de referencia (SQLAlchemy crea las tablas)
├── docker-compose.yml       # MySQL 8.0 + servidor Flask
├── Dockerfile
├── requirements.txt
└── run.py                   # Punto de entrada de la app
```

> **Base de datos:** el esquema lo crea automáticamente **SQLAlchemy** (`db.create_all()`) al iniciar la app. El archivo `database/init/01_schema.sql` es solo documentación/referencia, montado en `/docker-entrypoint-initdb.d`.

## Instalación

### Opción A — Con Docker (recomendada)

```bash
# 1. Copiar variables de entorno (valores por defecto listos para Docker)
cp .env.example .env

# 2. Construir y levantar los servicios
docker compose up --build
```

- App: http://localhost:5000
- Health check: http://localhost:5000/api/health

> Al primer arranque se crea la BD `unilibretour_db` desde cero y el seed inserta los usuarios por defecto.

### Opción B — Sin Docker (desarrollo local)

Requisitos: Python 3.12+ y MySQL 8.0 corriendo en local.

```bash
# 1. Crear la base de datos y el usuario en MySQL
mysql -u root -p -e "CREATE DATABASE unilibretour_db; CREATE USER 'unilibretour'@'localhost' IDENTIFIED BY 'unilibretour'; GRANT ALL PRIVILEGES ON unilibretour_db.* TO 'unilibretour'@'localhost'; FLUSH PRIVILEGES;"

# 2. Crear y activar el entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Variables de entorno (ajusta DATABASE_URL a tu MySQL si difiere)
#    En Windows PowerShell: $env:DATABASE_URL="mysql+pymysql://unilibretour:unilibretour@localhost:3306/unilibretour_db"

# 5. Ejecutar
python run.py
```

## Endpoints de la API

| Método | Ruta | Descripción | Autenticación |
|--------|------|-------------|---------------|
| GET | `/api/health` | Estado del servidor | — |
| POST | `/api/auth/login` | Iniciar sesión, retorna JWT | — |
| GET | `/api/usuarios` | Listar usuarios | — |
| GET | `/api/usuarios/<id>` | Obtener usuario por ID | — |
| POST | `/api/usuarios` | Crear usuario | — |
| PUT | `/api/usuarios/<id>` | Actualizar usuario | — |
| DELETE | `/api/usuarios/<id>` | Eliminar usuario | **admin** |

### Formato de respuesta

Todas las respuestas JSON usan un formato consistente:

```json
{ "ok": true,  "data": { ... } }
{ "ok": false, "error": "mensaje de error" }
```

En errores de validación, `error` contiene el diccionario de errores de Marshmallow.

### Login de ejemplo

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@unilibretour.edu.co", "password": "admin123"}'
```

## Usuarios por defecto (seed)

El seed se ejecuta automáticamente al iniciar la app (solo si la tabla `usuarios` está vacía).

| Rol | Email | Contraseña |
|-----|-------|-----------|
| admin | `admin@unilibretour.edu.co` | `admin123` |
| visitante | `estudiante@unilibretour.edu.co` | `visitante123` |