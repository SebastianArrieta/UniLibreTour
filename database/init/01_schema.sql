-- ============================================================
-- UniLibreTour — Esquema de referencia (SOLO DOCUMENTACIÓN)
-- ============================================================
-- NOTA IMPORTANTE:
-- SQLAlchemy es responsable de crear y mantener el esquema de la
-- base de datos a través de `db.create_all()` (ver app/__init__.py).
--
-- Este archivo NO se usa para crear tablas en producción. Se monta
-- en /docker-entrypoint-initdb.d solo como referencia/backup y para
-- dejar documentada la estructura esperada.
-- Si cambias los modelos en app/models, actualiza este archivo.
-- ============================================================

CREATE TABLE IF NOT EXISTS semilleros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    categoria VARCHAR(100),
    lider_id INT,
    descripcion TEXT,
    imagen VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'visitante' NOT NULL,
    estado VARCHAR(20) DEFAULT 'activo' NOT NULL,
    puntos INT DEFAULT 0 NOT NULL,
    nivel INT DEFAULT 1 NOT NULL,
    semillero_id INT,
    two_factor_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    anio_grado INT,
    cargo_actual VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (semillero_id) REFERENCES semilleros(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE semilleros
    ADD CONSTRAINT fk_semillero_lider FOREIGN KEY (lider_id) REFERENCES usuarios(id);

CREATE TABLE IF NOT EXISTS notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    mensaje VARCHAR(255) NOT NULL,
    tipo VARCHAR(50),
    referencia_tipo VARCHAR(50),
    referencia_id INT,
    leido BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS colecciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) UNIQUE,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    icono VARCHAR(100),
    imagen VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS etiquetas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(80) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS contenidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    categoria VARCHAR(100),
    descripcion TEXT,
    fecha VARCHAR(20),
    imagen VARCHAR(255),
    autor VARCHAR(150),
    estado VARCHAR(20) DEFAULT 'borrador' NOT NULL,
    observaciones TEXT,
    validado_por INT,
    fecha_validacion DATETIME,
    creador_id INT,
    coleccion_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (validado_por) REFERENCES usuarios(id),
    FOREIGN KEY (creador_id) REFERENCES usuarios(id),
    FOREIGN KEY (coleccion_id) REFERENCES colecciones(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS contenido_etiquetas (
    contenido_id INT NOT NULL,
    etiqueta_id INT NOT NULL,
    PRIMARY KEY (contenido_id, etiqueta_id),
    FOREIGN KEY (contenido_id) REFERENCES contenidos(id),
    FOREIGN KEY (etiqueta_id) REFERENCES etiquetas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS insignias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    icono VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS usuarios_insignias (
    usuario_id INT NOT NULL,
    insignia_id INT NOT NULL,
    fecha_obtenida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, insignia_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (insignia_id) REFERENCES insignias(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS premios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    anio INT,
    lugar VARCHAR(200),
    descripcion TEXT,
    categoria VARCHAR(100),
    imagen VARCHAR(255),
    estado VARCHAR(20) DEFAULT 'borrador' NOT NULL,
    observaciones TEXT,
    validado_por INT,
    fecha_validacion DATETIME,
    creador_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (validado_por) REFERENCES usuarios(id),
    FOREIGN KEY (creador_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cronologia_hitos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    anio INT,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(50),
    contenido_id INT,
    estado VARCHAR(20) DEFAULT 'borrador' NOT NULL,
    observaciones TEXT,
    validado_por INT,
    fecha_validacion DATETIME,
    creador_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (validado_por) REFERENCES usuarios(id),
    FOREIGN KEY (creador_id) REFERENCES usuarios(id),
    FOREIGN KEY (contenido_id) REFERENCES contenidos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS eventos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    fecha VARCHAR(20),
    hora VARCHAR(10),
    ubicacion VARCHAR(200),
    tipo VARCHAR(50),
    descripcion TEXT,
    estado VARCHAR(20) DEFAULT 'borrador' NOT NULL,
    observaciones TEXT,
    validado_por INT,
    fecha_validacion DATETIME,
    creador_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (validado_por) REFERENCES usuarios(id),
    FOREIGN KEY (creador_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS hall_de_la_fama (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    titulo VARCHAR(200),
    anio INT,
    logro TEXT,
    categoria VARCHAR(100),
    imagen VARCHAR(255),
    estado VARCHAR(20) DEFAULT 'borrador' NOT NULL,
    observaciones TEXT,
    validado_por INT,
    fecha_validacion DATETIME,
    creador_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (validado_por) REFERENCES usuarios(id),
    FOREIGN KEY (creador_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS noticias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    resumen TEXT,
    fecha VARCHAR(20),
    categoria VARCHAR(100),
    imagen VARCHAR(255),
    estado VARCHAR(20) DEFAULT 'borrador' NOT NULL,
    observaciones TEXT,
    validado_por INT,
    fecha_validacion DATETIME,
    creador_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (validado_por) REFERENCES usuarios(id),
    FOREIGN KEY (creador_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
