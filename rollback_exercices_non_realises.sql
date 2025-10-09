-- Script PostgreSQL de ROLLBACK pour annuler les modifications
-- À utiliser UNIQUEMENT si vous devez revenir en arrière
-- ATTENTION : Cela supprimera les données de raison_non_realise !

-- 1. Supprimer la contrainte CHECK
ALTER TABLE gestion_evaluationexercice 
DROP CONSTRAINT IF EXISTS gestion_evaluationexercice_raison_check;

-- 2. Supprimer la colonne raison_non_realise
ALTER TABLE gestion_evaluationexercice 
DROP COLUMN IF EXISTS raison_non_realise;

-- 3. Remettre la contrainte NOT NULL sur la colonne note
-- ATTENTION : Cette commande échouera s'il existe des lignes avec note = NULL
-- Dans ce cas, vous devez d'abord supprimer ou mettre à jour ces lignes
ALTER TABLE gestion_evaluationexercice 
ALTER COLUMN note SET NOT NULL;

-- 4. Vérifier que le rollback a bien été appliqué
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'gestion_evaluationexercice' 
ORDER BY column_name;

