-- PostgreSQL équivalent à la migration Django 0025_corps_mail_pdf_palanquees
-- Modèle : gestion.CorpsMailPdfPalanquees (singleton pk=1 pour le corps HTML du mail PDF palanquées)
--
-- Après exécution sur la base de production, si la migration n’est pas enregistrée dans Django :
--   python manage.py migrate gestion 0025 --fake
--
-- Vérification du nom de table (si besoin) :
--   SELECT table_name FROM information_schema.tables
--   WHERE table_schema = 'public' AND table_name LIKE '%corps%palanque%';

BEGIN;

CREATE TABLE IF NOT EXISTS gestion_corpsmailpdfpalanquees (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    corps_html TEXT NOT NULL DEFAULT ''
);

COMMIT;
