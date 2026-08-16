# UniLibreTour

Museo Digital Interactivo — proyecto de grado.

Stack: HTML5 · CSS3 + Tailwind CLI · TypeScript · Web Components · Node.js (`http` nativo) · PostgreSQL (`pg`) · Docker.

---

## Estructura del proyecto

```
UniLibreTour/
├── .env.example              # Variables de entorno de referencia
├── .gitignore
├── docker-compose.yml        # Entorno local: servidor + PostgreSQL
├── Dockerfile                # Imagen del servidor para despliegue
├── package.json              # Scripts y dependencias del monorepo
├── tsconfig.base.json        # Opciones TypeScript compartidas
│
├── frontend/                 # Capa de presentación (sin framework de UI)
│   ├── tailwind.config.js    # Configuración Tailwind CLI
│   ├── tsconfig.json
│   ├── pages/                # Pantallas HTML (10+ páginas del museo)
│   ├── components/           # Web Components (Custom Elements)
│   ├── scripts/
│   │   ├── pages/            # Lógica TypeScript por pantalla
│   │   ├── utils/            # Utilidades compartidas del cliente
│   │   └── types/            # Tipos TypeScript del frontend
│   ├── styles/
│   │   └── input.css         # Entrada Tailwind → compilada a public/css/
│   ├── assets/
│   │   ├── images/
│   │   └── fonts/
│   └── public/               # Artefactos estáticos servidos al navegador
│       ├── css/              # CSS compilado (Tailwind)
│       └── js/               # JS compilado (TypeScript)
│
├── backend/                  # Servidor Node.js sin Express/Fastify
│   ├── tsconfig.json
│   └── src/
│       ├── index.ts          # Punto de entrada del servidor HTTP
│       ├── router/           # Enrutamiento manual (método + URL)
│       ├── controllers/      # Manejo de peticiones y respuestas
│       ├── models/           # Consultas SQL con driver pg (sin ORM)
│       ├── middleware/       # Auth, sesiones, validación de roles
│       ├── services/         # Lógica de negocio reutilizable
│       ├── types/            # Tipos del dominio (Usuario, Proyecto, etc.)
│       ├── utils/            # Helpers del servidor
│       └── config/           # Conexión BD, variables de entorno
│
└── database/                 # Esquema y datos PostgreSQL
    ├── init/                 # Scripts SQL al levantar Docker (desarrollo)
    ├── migrations/           # Cambios de esquema versionados
    └── seeds/                # Datos iniciales de prueba
```

---

## Responsabilidad de cada capa

| Carpeta | Tecnología | Rol |
|---------|-----------|-----|
| `frontend/pages` | HTML5 | Marcado semántico de cada pantalla |
| `frontend/components` | Web Components | UI reutilizable (`<header-museo>`, modales, tarjetas) |
| `frontend/styles` + `public/css` | Tailwind CLI | Estilos compilados a un único CSS |
| `frontend/scripts` | TypeScript → JS | Lógica del cliente sin framework |
| `backend/src/router` | Node.js `http` | Despacho manual de rutas |
| `backend/src/models` | `pg` | SQL escrito a mano, sin ORM |
| `backend/src/middleware` | bcrypt + cookies | Autenticación y control de roles |
| `database/` | PostgreSQL | Esquema, migraciones y seeds |
| Raíz (`Dockerfile`, `docker-compose.yml`) | Docker | Entorno reproducible local y empaquetado |

---

## Entornos

- **Desarrollo local:** `docker compose up` levanta servidor + Postgres.
- **Producción:** imagen Docker en Render/Railway + base de datos en Neon.

Copia `.env.example` a `.env` y ajusta los valores antes de desarrollar.
