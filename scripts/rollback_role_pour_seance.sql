-- Script PostgreSQL pour supprimer le champ role_pour_seance de la table gestion_inscriptionseance
-- ATTENTION : Ce script supprime définitivement la colonne et toutes ses données
-- Utilisez ce script uniquement si vous souhaitez annuler l'évolution

-- Étape 1 : Supprimer la contrainte CHECK
ALTER TABLE gestion_inscriptionseance 
DROP CONSTRAINT IF EXISTS gestion_inscriptionseance_role_pour_seance_check;

-- Étape 2 : Supprimer la colonne role_pour_seance
ALTER TABLE gestion_inscriptionseance 
DROP COLUMN IF EXISTS role_pour_seance;

-- Vérification : Confirmer que la colonne a été supprimée
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'gestion_inscriptionseance' 
AND column_name = 'role_pour_seance';

-- Si la requête ci-dessus ne retourne aucune ligne, la colonne a bien été supprimée

