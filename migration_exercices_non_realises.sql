-- Script PostgreSQL pour ajouter la gestion des exercices non réalisés
-- À exécuter sur la base de données de production

-- 1. Modifier la colonne 'note' pour accepter NULL
ALTER TABLE gestion_evaluationexercice 
ALTER COLUMN note DROP NOT NULL;

-- 2. Ajouter la colonne 'raison_non_realise' avec les contraintes
ALTER TABLE gestion_evaluationexercice 
ADD COLUMN raison_non_realise VARCHAR(20) NULL;

-- 3. Ajouter une contrainte CHECK pour valider les valeurs de raison_non_realise
ALTER TABLE gestion_evaluationexercice 
ADD CONSTRAINT gestion_evaluationexercice_raison_check 
CHECK (raison_non_realise IN ('temps', 'apprehension', 'refus'));

-- 4. Ajouter un commentaire sur la colonne pour documentation
COMMENT ON COLUMN gestion_evaluationexercice.raison_non_realise IS 'Raison de non réalisation de l''exercice: temps=A court de temps, apprehension=Apprehension, refus=Refus de l''eleve';

-- 5. Vérifier que la modification a bien été appliquée
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'gestion_evaluationexercice' 
AND column_name IN ('note', 'raison_non_realise')
ORDER BY column_name;

-- 6. Afficher quelques statistiques
SELECT 
    COUNT(*) as total_evaluations,
    COUNT(note) as evaluations_avec_note,
    COUNT(raison_non_realise) as evaluations_non_realisees
FROM gestion_evaluationexercice;

