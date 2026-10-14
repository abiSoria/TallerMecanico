-- Permite asociar clientes existentes y nuevos a un taller.
-- La columna nullable conserva clientes históricos sin relación asignada.
USE taller_mecanico;

ALTER TABLE clients
  ADD COLUMN workshop_id INT NULL,
  ADD CONSTRAINT fk_clients_workshop FOREIGN KEY (workshop_id) REFERENCES workshops(id);
