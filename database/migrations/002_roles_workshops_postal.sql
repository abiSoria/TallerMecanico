-- TallerMecanico: roles administrables, estados relacionales, talleres y catálogo postal.
-- Ejecutar una sola vez con un usuario administrador de MySQL, en taller_mecanico.
USE taller_mecanico;

CREATE TABLE Estatus (
  IdEstatus INT PRIMARY KEY,
  Valor VARCHAR(20) NOT NULL UNIQUE,
  Descripcion VARCHAR(120) NOT NULL
) ENGINE=InnoDB;
INSERT INTO Estatus (IdEstatus, Valor, Descripcion) VALUES
 (1, 'Activo', 'Rol habilitado para su uso'),
 (2, 'Suspendido', 'Rol deshabilitado para su uso');

ALTER TABLE roles ADD COLUMN code VARCHAR(50) NULL;
ALTER TABLE roles ADD COLUMN normalized_name VARCHAR(40) NULL;
ALTER TABLE roles ADD COLUMN id_estatus INT NOT NULL DEFAULT 1;
UPDATE roles SET code = CASE name
  WHEN 'administrador' THEN 'administrador'
  WHEN 'recepcionista' THEN 'recepcionista'
  WHEN 'asesor_servicio' THEN 'asesor_servicio'
  WHEN 'tecnico' THEN 'tecnico'
  WHEN 'cliente' THEN 'cliente'
  WHEN 'sistema' THEN 'sistema'
  ELSE CONCAT('custom_', id)
END;
UPDATE roles SET normalized_name = LOWER(TRIM(name));
ALTER TABLE roles MODIFY code VARCHAR(50) NOT NULL;
ALTER TABLE roles MODIFY normalized_name VARCHAR(40) NOT NULL;
ALTER TABLE roles ADD CONSTRAINT uq_roles_code UNIQUE (code);
ALTER TABLE roles ADD CONSTRAINT uq_roles_normalized_name UNIQUE (normalized_name);
ALTER TABLE roles ADD CONSTRAINT fk_roles_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus);

ALTER TABLE users ADD COLUMN id_estatus INT NOT NULL DEFAULT 1;
UPDATE users SET id_estatus = IF(is_active, 1, 2);
ALTER TABLE users ADD CONSTRAINT fk_users_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus);
ALTER TABLE users DROP COLUMN is_active;

ALTER TABLE clients ADD COLUMN id_estatus INT NOT NULL DEFAULT 1;
UPDATE clients SET id_estatus = IF(is_active, 1, 2);
ALTER TABLE clients ADD CONSTRAINT fk_clients_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus);
ALTER TABLE clients DROP COLUMN is_active;

CREATE TABLE workshops (
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

CREATE TABLE postal_codes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  postal_code CHAR(5) NOT NULL,
  neighborhood VARCHAR(120) NOT NULL,
  municipality VARCHAR(120) NOT NULL,
  state VARCHAR(100) NOT NULL,
  CONSTRAINT uq_postal_location UNIQUE (postal_code, neighborhood, municipality, state),
  INDEX idx_postal_code (postal_code),
  INDEX idx_postal_reverse (state, municipality, neighborhood)
) ENGINE=InnoDB;
