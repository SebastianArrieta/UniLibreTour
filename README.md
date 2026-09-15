# UniLibreTour

Museo Digital Interactivo — proyecto de grado.

Stack: Python (`http.server`) · Arquitectura **MVC** · **MySQL 8.0** (`pymysql`) · **Jinja2** (Renderizado de Vistas) · JavaScript (ES6+) · Docker.

---

## Estructura del proyecto

```
UniLibreTour/
├── .env.example              # Variables de entorno de referencia
├── .gitignore
├── docker-compose.yml        # Entorno local: Servidor Python + MySQL
├── Dockerfile                # Imagen del servidor para despliegue
│
├── frontend/                 # Capa de presentación (Vistas Jinja2 y Cliente)
│   ├── pages/                # Plantillas Jinja2 (.html) renderizadas por el backend
│   ├── components/           # Componentes UI reutilizables
│   ├── scripts/              # Lógica de JavaScript del cliente
│   ├── styles/               # Hojas de estilo CSS
│   └── public/               # Artefactos estáticos servidos al navegador
│
├── backend/                  # Servidor Python en arquitectura MVC
│   ├── main.py               # Punto de entrada HTTP (`http.server`)
│   ├── router/               # Enrutador de peticiones (Web e API)
│   ├── controllers/          # Controladores (Manejo de rutas y Jinja2)
│   ├── models/               # Modelos (Consultas SQL a MySQL)
│   ├── middleware/           # Auth, sesiones, validación de roles
│   ├── services/             # Lógica de negocio reutilizable
│   ├── utils/                # Utilidades (Renderizador Jinja2 `template.py`, respuestas HTTP)
│   └── config/               # Conexión BD MySQL (`pymysql`) y variables
│
└── database/                 # Esquema y datos MySQL
    ├── init/                 # Scripts SQL ejecutados al levantar Docker
    ├── migrations/           # Cambios de esquema versionados
    └── seeds/                # Datos iniciales de prueba
```

---

## Responsabilidad de cada capa (MVC)

| Carpeta / Capa | Tecnología | Rol MVC |
|---------|-----------|-----|
| `frontend/pages` | **Jinja2 (HTML5)** | **Vista (V):** Plantillas dinámicas procesadas desde el servidor |
| `frontend/scripts` | **JavaScript (ES6)** | **Cliente:** Lógica interactiva en el navegador |
| `backend/controllers` | **Python** | **Controlador (C):** Maneja las peticiones y llama al renderizador Jinja2 o API JSON |
| `backend/models` | **PyMySQL** | **Modelo (M):** Consultas directas a la base de datos MySQL sin ORM |
| `database/` | **MySQL 8.0** | **Base de Datos:** Almacenamiento relacional |
| `docker-compose.yml` | **Docker** | **Infraestructura:** Entorno reproducible con MySQL y Servidor Python |

---

## Entornos

- **Desarrollo local:** `docker compose up --build` levanta el servidor Python y el contenedor de MySQL.

