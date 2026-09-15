-- Initial schema for MySQL
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'visitante',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seed inicial de prueba
INSERT IGNORE INTO usuarios (id, nombre, email, password_hash, rol) VALUES
(1, 'Administrador Museo', 'admin@unilibretour.edu.co', 'pbkdf2:sha256:dummy_hash', 'admin'),
(2, 'Estudiante Visita', 'estudiante@unilibretour.edu.co', 'pbkdf2:sha256:dummy_hash', 'visitante');
