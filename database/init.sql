-- Esquema inicial actualizado. Ejecutar con un usuario administrador de MySQL.
CREATE DATABASE IF NOT EXISTS taller_mecanico CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER IF NOT EXISTS 'taller_app'@'localhost' IDENTIFIED BY 'CAMBIA_ESTA_CLAVE';
GRANT SELECT, INSERT, UPDATE, DELETE ON taller_mecanico.* TO 'taller_app'@'localhost';
FLUSH PRIVILEGES;
USE taller_mecanico;

CREATE TABLE IF NOT EXISTS Estatus (
  IdEstatus INT PRIMARY KEY,
  Valor VARCHAR(20) NOT NULL UNIQUE,
  Descripcion VARCHAR(120) NOT NULL
) ENGINE=InnoDB;
INSERT INTO Estatus (IdEstatus, Valor, Descripcion) VALUES
 (1, 'Activo', 'Rol habilitado para su uso'),
 (2, 'Suspendido', 'Rol deshabilitado para su uso')
ON DUPLICATE KEY UPDATE Valor=VALUES(Valor), Descripcion=VALUES(Descripcion);

CREATE TABLE IF NOT EXISTS roles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(40) NOT NULL UNIQUE,
  normalized_name VARCHAR(40) NOT NULL UNIQUE,
  description VARCHAR(200),
  id_estatus INT NOT NULL DEFAULT 1,
  CONSTRAINT fk_roles_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  role_id INT NOT NULL,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  id_estatus INT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id),
  CONSTRAINT fk_users_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus),
  INDEX idx_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS clients (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name TEXT NOT NULL, street TEXT NOT NULL, number TEXT NOT NULL,
  neighborhood TEXT NOT NULL, municipality TEXT NOT NULL, state TEXT NOT NULL,
  primary_phone TEXT NOT NULL, alternate_phone TEXT NOT NULL, email TEXT NOT NULL,
  id_estatus INT NOT NULL DEFAULT 1,
  CONSTRAINT fk_clients_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workshops (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL,
  rfc VARCHAR(13) NOT NULL UNIQUE,
  contact_email VARCHAR(254) NOT NULL,
  street VARCHAR(160) NOT NULL,
  number VARCHAR(30) NOT NULL,
  postal_code CHAR(5) NOT NULL,
  state VARCHAR(100) NOT NULL,
  municipality VARCHAR(120) NOT NULL,
  neighborhood VARCHAR(120) NOT NULL,
  photo_filename VARCHAR(80) NOT NULL,
  id_estatus INT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_workshops_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS postal_codes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  postal_code CHAR(5) NOT NULL,
  neighborhood VARCHAR(120) NOT NULL,
  municipality VARCHAR(120) NOT NULL,
  state VARCHAR(100) NOT NULL,
  CONSTRAINT uq_postal_location UNIQUE (postal_code, neighborhood, municipality, state),
  INDEX idx_postal_code (postal_code),
  INDEX idx_postal_reverse (state, municipality, neighborhood)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vehicles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  client_id INT NOT NULL, plate VARCHAR(12) NOT NULL UNIQUE,
  make VARCHAR(60) NOT NULL, model VARCHAR(60) NOT NULL, year SMALLINT,
  CONSTRAINT fk_vehicles_client FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS repair_orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  vehicle_id INT NOT NULL, status VARCHAR(40) NOT NULL DEFAULT 'recibido',
  description TEXT NOT NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_orders_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
  INDEX idx_orders_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id INT, action VARCHAR(80) NOT NULL, detail TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_audit_created (created_at)
) ENGINE=InnoDB;

INSERT IGNORE INTO roles (code, name, normalized_name, description, id_estatus) VALUES
 ('administrador', 'administrador', 'administrador', 'Gestión completa del taller y configuración', 1),
 ('recepcionista', 'recepcionista', 'recepcionista', 'Registro y actualización de datos operativos', 1),
 ('asesor_servicio', 'asesor_servicio', 'asesor_servicio', 'Consulta de datos y seguimiento de órdenes', 1),
 ('tecnico', 'tecnico', 'tecnico', 'Diagnóstico y actualización de reparaciones', 1),
 ('cliente', 'cliente', 'cliente', 'Consulta de sus vehículos y órdenes', 1),
 ('sistema', 'sistema', 'sistema', 'Procesos automáticos y auditoría interna', 1);
