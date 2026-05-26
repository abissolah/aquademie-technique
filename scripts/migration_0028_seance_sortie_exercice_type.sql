BEGIN;

ALTER TABLE gestion_exercice
    ADD COLUMN IF NOT EXISTS type varchar(20) NOT NULL DEFAULT 'classique';

ALTER TABLE gestion_seance
    ADD COLUMN IF NOT EXISTS type varchar(20) NOT NULL DEFAULT 'seance';

ALTER TABLE gestion_seance
    ALTER COLUMN lieu_id DROP NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'seance_lieu_required_for_classic_seance'
    ) THEN
        ALTER TABLE gestion_seance
            ADD CONSTRAINT seance_lieu_required_for_classic_seance
            CHECK (type = 'sortie' OR lieu_id IS NOT NULL);
    END IF;
END$$;

COMMIT;
