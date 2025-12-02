-- Script SQL pour créer la table gestion_listediffusion et sa table de liaison
-- PostgreSQL
--
-- IMPORTANT: Avant d'exécuter ce script, vérifiez les noms de tables dans votre base de données :
-- - La table des utilisateurs peut être 'auth_user' (par défaut) ou autre si AUTH_USER_MODEL est personnalisé
-- - La table des adhérents devrait être 'gestion_adherent'
-- 
-- Pour vérifier les noms de tables, exécutez :
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%user%' OR tablename LIKE '%adherent%';

-- 1. Créer la table principale gestion_listediffusion
CREATE TABLE gestion_listediffusion (
    id BIGSERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    date_creation TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    auteur_id INTEGER NULL,
    CONSTRAINT gestion_listediffusion_auteur_id_fkey 
        FOREIGN KEY (auteur_id) 
        REFERENCES auth_user(id) 
        ON DELETE SET NULL
);

-- 2. Créer la table de liaison pour la relation ManyToMany avec Adherent
CREATE TABLE gestion_listediffusion_adherents (
    id BIGSERIAL PRIMARY KEY,
    listediffusion_id BIGINT NOT NULL,
    adherent_id BIGINT NOT NULL,
    CONSTRAINT gestion_listediffusion_adherents_listediffusion_id_fkey 
        FOREIGN KEY (listediffusion_id) 
        REFERENCES gestion_listediffusion(id) 
        ON DELETE CASCADE,
    CONSTRAINT gestion_listediffusion_adherents_adherent_id_fkey 
        FOREIGN KEY (adherent_id) 
        REFERENCES gestion_adherent(id) 
        ON DELETE CASCADE,
    CONSTRAINT gestion_listediffusion_adherents_listediffusion_id_adherent_id_unique 
        UNIQUE (listediffusion_id, adherent_id)
);

-- 3. Créer les index pour améliorer les performances
CREATE INDEX gestion_listediffusion_auteur_id_idx ON gestion_listediffusion(auteur_id);
CREATE INDEX gestion_listediffusion_adherents_listediffusion_id_idx ON gestion_listediffusion_adherents(listediffusion_id);
CREATE INDEX gestion_listediffusion_adherents_adherent_id_idx ON gestion_listediffusion_adherents(adherent_id);

-- 4. Ajouter les commentaires pour la documentation
COMMENT ON TABLE gestion_listediffusion IS 'Listes de diffusion personnalisées pour les adhérents';
COMMENT ON COLUMN gestion_listediffusion.nom IS 'Nom de la liste de diffusion';
COMMENT ON COLUMN gestion_listediffusion.date_creation IS 'Date de création de la liste';
COMMENT ON COLUMN gestion_listediffusion.auteur_id IS 'Utilisateur ayant créé la liste';

COMMENT ON TABLE gestion_listediffusion_adherents IS 'Table de liaison entre les listes de diffusion et les adhérents';
COMMENT ON COLUMN gestion_listediffusion_adherents.listediffusion_id IS 'Référence à la liste de diffusion';
COMMENT ON COLUMN gestion_listediffusion_adherents.adherent_id IS 'Référence à l''adhérent';

