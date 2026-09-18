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

-- Tabla usuarios (equivalente a app/models/usuario.py)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'visitante',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
