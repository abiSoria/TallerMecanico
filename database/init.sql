-- Ejecutar como usuario administrador de MySQL. Cambia la clave del usuario de aplicación.
CREATE DATABASE IF NOT EXISTS taller_mecanico
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS 'taller_app'@'localhost' IDENTIFIED BY 'CAMBIA_ESTA_CLAVE';
GRANT SELECT, INSERT, UPDATE, DELETE ON taller_mecanico.* TO 'taller_app'@'localhost';
FLUSH PRIVILEGES;
USE taller_mecanico;

CREATE TABLE IF NOT EXISTS roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(40) NOT NULL UNIQUE,
  description VARCHAR(200)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  role_id INT NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id),
  INDEX idx_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS clients (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNIQUE,
  phone VARCHAR(20),
  CONSTRAINT fk_clients_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vehicles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  client_id INT NOT NULL,
  plate VARCHAR(12) NOT NULL UNIQUE,
  make VARCHAR(60) NOT NULL,
  model VARCHAR(60) NOT NULL,
  year SMALLINT,
  CONSTRAINT fk_vehicles_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS repair_orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL,
  status VARCHAR(40) NOT NULL DEFAULT 'recibido',
  description TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_orders_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
  INDEX idx_orders_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id INT,
  action VARCHAR(80) NOT NULL,
  detail TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_audit_created (created_at)
) ENGINE=InnoDB;

INSERT IGNORE INTO roles (name, description) VALUES
 ('administrador', 'Gestión completa del taller y configuración'),
 ('recepcionista', 'Registro y actualización de datos operativos'),
 ('asesor_servicio', 'Consulta de datos y seguimiento de órdenes'),
 ('tecnico', 'Diagnóstico y actualización de reparaciones'),
 ('cliente', 'Consulta de sus vehículos y órdenes'),
 ('sistema', 'Procesos automáticos y auditoría interna');

