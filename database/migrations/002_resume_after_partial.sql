-- Continuación de 002_roles_workshops_postal.sql después de una ejecución parcial.
-- Ejecutar solo si el estado coincide con el verificado el 2026-10-09:
-- Estatus contiene IdEstatus 1 y 2; roles ya tiene code, normalized_name e id_estatus,
-- pero code y normalized_name aún están NULL; users/clients conservan is_active y
-- no tienen id_estatus; workshops y postal_codes todavía no existen.
-- Hacer respaldo antes de ejecutar. No ejecutar junto con la migración 002 original.
USE taller_mecanico;

UPDATE roles SET code = CASE name
  WHEN 'administrador' THEN 'administrador'
  WHEN 'recepcionista' THEN 'recepcionista'
  WHEN 'asesor_servicio' THEN 'asesor_servicio'
  WHEN 'tecnico' THEN 'tecnico'
  WHEN 'cliente' THEN 'cliente'
  WHEN 'sistema' THEN 'sistema'
  ELSE CONCAT('custom_', id)
END
WHERE id >= 1;
UPDATE roles SET normalized_name = LOWER(TRIM(name)) WHERE id >= 1;
ALTER TABLE roles MODIFY code VARCHAR(50) NOT NULL;
ALTER TABLE roles MODIFY normalized_name VARCHAR(40) NOT NULL;
ALTER TABLE roles ADD CONSTRAINT uq_roles_code UNIQUE (code);
ALTER TABLE roles ADD CONSTRAINT uq_roles_normalized_name UNIQUE (normalized_name);
ALTER TABLE roles ADD CONSTRAINT fk_roles_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus);

ALTER TABLE users ADD COLUMN id_estatus INT NOT NULL DEFAULT 1;
UPDATE users SET id_estatus = IF(is_active, 1, 2) WHERE id >= 1;
ALTER TABLE users ADD CONSTRAINT fk_users_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus);
ALTER TABLE users DROP COLUMN is_active;

ALTER TABLE clients ADD COLUMN id_estatus INT NOT NULL DEFAULT 1;
UPDATE clients SET id_estatus = IF(is_active, 1, 2) WHERE id >= 1;
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
