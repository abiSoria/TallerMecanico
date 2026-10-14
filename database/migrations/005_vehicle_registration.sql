-- Extiende vehicles sin modificar registros históricos ni la relación existente con clients.
USE taller_mecanico;

ALTER TABLE vehicles
  ADD COLUMN vin VARCHAR(32) NULL,
  ADD COLUMN version VARCHAR(80) NULL,
  ADD COLUMN color VARCHAR(40) NULL,
  ADD COLUMN mileage INT NULL,
  ADD COLUMN photo_filename VARCHAR(80) NULL,
  ADD COLUMN id_estatus INT NOT NULL DEFAULT 1,
  ADD CONSTRAINT uq_vehicles_vin UNIQUE (vin),
  ADD CONSTRAINT fk_vehicles_estatus FOREIGN KEY (id_estatus) REFERENCES Estatus(IdEstatus);
