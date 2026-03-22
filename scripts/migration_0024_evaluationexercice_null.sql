-- Script PostgreSQL équivalent à la migration 0024_evaluationexercice_null_palanquee_encadrant
-- Rendre nullable les champs palanquee_id et encadrant_id de gestion_evaluationexercice
-- (pour validation DT : évaluation sans palanquée/encadrant)

BEGIN;

-- Rendre palanquee_id nullable
ALTER TABLE gestion_evaluationexercice
    ALTER COLUMN palanquee_id DROP NOT NULL;

-- Rendre encadrant_id nullable
ALTER TABLE gestion_evaluationexercice
    ALTER COLUMN encadrant_id DROP NOT NULL;

COMMIT;
