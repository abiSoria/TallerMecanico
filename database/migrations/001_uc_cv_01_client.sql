-- Actualiza clients al contrato de UC-CV-01.
-- Aplicar una sola vez tras respaldar la base de datos.
ALTER TABLE clients
  DROP FOREIGN KEY fk_clients_user,
  DROP COLUMN user_id,
  DROP COLUMN phone,
  ADD COLUMN full_name TEXT NOT NULL,
  ADD COLUMN street TEXT NOT NULL,
  ADD COLUMN number TEXT NOT NULL,
  ADD COLUMN neighborhood TEXT NOT NULL,
  ADD COLUMN municipality TEXT NOT NULL,
  ADD COLUMN state TEXT NOT NULL,
  ADD COLUMN primary_phone TEXT NOT NULL,
  ADD COLUMN alternate_phone TEXT NOT NULL,
  ADD COLUMN email TEXT NOT NULL,
  ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
