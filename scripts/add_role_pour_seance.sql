-- Script PostgreSQL pour ajouter le champ role_pour_seance à la table gestion_inscriptionseance
-- Cette évolution permet de passer un encadrant en élève pour une séance spécifique

-- Étape 1 : Ajouter la colonne role_pour_seance avec une valeur par défaut temporaire
ALTER TABLE gestion_inscriptionseance 
ADD COLUMN role_pour_seance VARCHAR(20) DEFAULT 'encadrant' NOT NULL;

-- Étape 2 : Mettre à jour toutes les lignes existantes avec la valeur par défaut 'encadrant'
-- (Cette étape est déjà faite par la valeur par défaut, mais on la fait explicitement pour être sûr)
UPDATE gestion_inscriptionseance 
SET role_pour_seance = 'encadrant' 
WHERE role_pour_seance IS NULL;

-- Étape 3 : Ajouter une contrainte CHECK pour s'assurer que seules les valeurs autorisées sont acceptées
ALTER TABLE gestion_inscriptionseance 
ADD CONSTRAINT gestion_inscriptionseance_role_pour_seance_check 
CHECK (role_pour_seance IN ('encadrant', 'eleve'));

-- Étape 4 : Ajouter un commentaire sur la colonne pour la documentation
COMMENT ON COLUMN gestion_inscriptionseance.role_pour_seance IS 
'Rôle pour cette séance : encadrant (par défaut) ou eleve (passer en élève pour la séance)';

-- Vérification : Afficher un résumé des modifications
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    column_default,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'gestion_inscriptionseance' 
AND column_name = 'role_pour_seance';

-- Vérification : Compter les inscriptions par rôle
SELECT 
    role_pour_seance,
    COUNT(*) as nombre_inscriptions
FROM gestion_inscriptionseance
GROUP BY role_pour_seance;

