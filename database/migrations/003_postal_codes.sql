-- Crea el catálogo local requerido por las búsquedas de códigos postales.
-- La consulta devuelve resultados hasta importar el TXT oficial de SEPOMEX.
USE taller_mecanico;

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
