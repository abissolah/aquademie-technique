-- Script SQL pour supprimer la contrainte unique sur (eleve_id, exercice_id) 
-- de la table gestion_evaluationexercice

-- Supprimer la contrainte unique existante
ALTER TABLE gestion_evaluationexercice 
DROP CONSTRAINT IF EXISTS gestion_evaluationexercice_eleve_id_exercice_id_024bf491_uniq;

-- Alternative si le nom de la contrainte est différent
-- Vous pouvez vérifier le nom exact de la contrainte avec cette requête :
-- SELECT constraint_name 
-- FROM information_schema.table_constraints 
-- WHERE table_name = 'gestion_evaluationexercice' 
-- AND constraint_type = 'UNIQUE';

-- Si le nom de la contrainte est différent, utilisez cette syntaxe :
-- ALTER TABLE gestion_evaluationexercice 
-- DROP CONSTRAINT nom_exact_de_la_contrainte;







