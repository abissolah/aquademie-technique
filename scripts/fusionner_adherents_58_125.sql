-- Script SQL pour fusionner l'adhérent 125 vers l'adhérent 58
-- ATTENTION: Exécuter ce script avec précaution en production
-- Il est recommandé de faire une sauvegarde de la base de données avant

BEGIN;

-- ============================================
-- 1. GESTION DES CONTRAINTES D'UNICITÉ
-- ============================================

-- Supprimer les inscriptions en double (si l'adhérent 58 est déjà inscrit aux mêmes séances que 125)
DELETE FROM gestion_inscriptionseance
WHERE personne_id = 125
  AND seance_id IN (
    SELECT seance_id FROM gestion_inscriptionseance WHERE personne_id = 58
  );

-- Supprimer les palanquées élèves en double (si l'adhérent 58 est déjà dans les mêmes palanquées que 125)
DELETE FROM gestion_palanqueeleve
WHERE eleve_id = 125
  AND palanquee_id IN (
    SELECT palanquee_id FROM gestion_palanqueeleve WHERE eleve_id = 58
  );

-- Supprimer les évaluations en double (si l'adhérent 58 a déjà été évalué pour les mêmes compétences dans les mêmes palanquées)
DELETE FROM gestion_evaluation
WHERE eleve_id = 125
  AND (palanquee_id, competence_id) IN (
    SELECT palanquee_id, competence_id FROM gestion_evaluation WHERE eleve_id = 58
  );

-- ============================================
-- 2. MISE À JOUR DES FOREIGN KEYS
-- ============================================

-- Mettre à jour les séances où l'adhérent 125 était directeur de plongée
UPDATE gestion_seance
SET directeur_plongee_id = 58
WHERE directeur_plongee_id = 125;

-- Mettre à jour les palanquées où l'adhérent 125 était encadrant
UPDATE gestion_palanquee
SET encadrant_id = 58
WHERE encadrant_id = 125;

-- Mettre à jour les inscriptions aux séances
UPDATE gestion_inscriptionseance
SET personne_id = 58
WHERE personne_id = 125;

-- Mettre à jour les palanquées élèves (si l'adhérent 125 était élève dans certaines palanquées)
UPDATE gestion_palanqueeleve
SET eleve_id = 58
WHERE eleve_id = 125;

-- Mettre à jour les évaluations où l'adhérent 125 était évalué
UPDATE gestion_evaluation
SET eleve_id = 58
WHERE eleve_id = 125;

-- Mettre à jour les évaluations d'exercices où l'adhérent 125 était évalué (en tant qu'élève)
UPDATE gestion_evaluationexercice
SET eleve_id = 58
WHERE eleve_id = 125;

-- Mettre à jour les évaluations d'exercices où l'adhérent 125 était évaluateur (en tant qu'encadrant)
UPDATE gestion_evaluationexercice
SET encadrant_id = 58
WHERE encadrant_id = 125;

-- ============================================
-- 3. MISE À JOUR DES RELATIONS MANY-TO-MANY
-- ============================================

-- Transférer les sections de l'adhérent 125 vers l'adhérent 58
-- (en évitant les doublons)
INSERT INTO gestion_adherent_sections (adherent_id, section_id)
SELECT 58, section_id
FROM gestion_adherent_sections
WHERE adherent_id = 125
  AND section_id NOT IN (
    SELECT section_id FROM gestion_adherent_sections WHERE adherent_id = 58
  );

-- Supprimer les sections de l'adhérent 125 (maintenant transférées)
DELETE FROM gestion_adherent_sections
WHERE adherent_id = 125;

-- Transférer les listes de diffusion de l'adhérent 125 vers l'adhérent 58
-- (en évitant les doublons)
INSERT INTO gestion_listediffusion_adherents (listediffusion_id, adherent_id)
SELECT listediffusion_id, 58
FROM gestion_listediffusion_adherents
WHERE adherent_id = 125
  AND (listediffusion_id, 58) NOT IN (
    SELECT listediffusion_id, adherent_id FROM gestion_listediffusion_adherents WHERE adherent_id = 58
  );

-- Supprimer les listes de diffusion de l'adhérent 125 (maintenant transférées)
DELETE FROM gestion_listediffusion_adherents
WHERE adherent_id = 125;

-- ============================================
-- 4. GESTION DU COMPTE UTILISATEUR (User)
-- ============================================

-- Si l'adhérent 125 a un compte utilisateur et que l'adhérent 58 n'en a pas,
-- transférer le compte utilisateur
UPDATE gestion_adherent
SET user_id = (
  SELECT user_id FROM gestion_adherent WHERE id = 125
)
WHERE id = 58
  AND user_id IS NULL
  AND EXISTS (
    SELECT 1 FROM gestion_adherent WHERE id = 125 AND user_id IS NOT NULL
  );

-- Si les deux ont un compte utilisateur, on garde celui de l'adhérent 58
-- (on ne fait rien dans ce cas, ou on peut supprimer le compte de 125 si nécessaire)

-- ============================================
-- 5. SUPPRESSION DE L'ADHÉRENT 125
-- ============================================

-- Vérifier qu'il ne reste plus de références à l'adhérent 125
-- (ces vérifications devraient toutes retourner 0)

-- Vérification des séances
DO $$
DECLARE
    count_seances INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_seances FROM gestion_seance WHERE directeur_plongee_id = 125;
    IF count_seances > 0 THEN
        RAISE EXCEPTION 'Il reste % séance(s) référençant l''adhérent 125', count_seances;
    END IF;
END $$;

-- Vérification des palanquées
DO $$
DECLARE
    count_palanquees INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_palanquees FROM gestion_palanquee WHERE encadrant_id = 125;
    IF count_palanquees > 0 THEN
        RAISE EXCEPTION 'Il reste % palanquée(s) référençant l''adhérent 125', count_palanquees;
    END IF;
END $$;

-- Vérification des inscriptions
DO $$
DECLARE
    count_inscriptions INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_inscriptions FROM gestion_inscriptionseance WHERE personne_id = 125;
    IF count_inscriptions > 0 THEN
        RAISE EXCEPTION 'Il reste % inscription(s) référençant l''adhérent 125', count_inscriptions;
    END IF;
END $$;

-- Vérification des palanquées élèves
DO $$
DECLARE
    count_palanqueeleve INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_palanqueeleve FROM gestion_palanqueeleve WHERE eleve_id = 125;
    IF count_palanqueeleve > 0 THEN
        RAISE EXCEPTION 'Il reste % palanquée(s) élève référençant l''adhérent 125', count_palanqueeleve;
    END IF;
END $$;

-- Vérification des évaluations
DO $$
DECLARE
    count_evaluations INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_evaluations FROM gestion_evaluation WHERE eleve_id = 125;
    IF count_evaluations > 0 THEN
        RAISE EXCEPTION 'Il reste % évaluation(s) référençant l''adhérent 125', count_evaluations;
    END IF;
END $$;

-- Vérification des évaluations d'exercices
DO $$
DECLARE
    count_eval_exercices INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_eval_exercices FROM gestion_evaluationexercice 
    WHERE eleve_id = 125 OR encadrant_id = 125;
    IF count_eval_exercices > 0 THEN
        RAISE EXCEPTION 'Il reste % évaluation(s) d''exercices référençant l''adhérent 125', count_eval_exercices;
    END IF;
END $$;

-- Vérification des sections
DO $$
DECLARE
    count_sections INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_sections FROM gestion_adherent_sections WHERE adherent_id = 125;
    IF count_sections > 0 THEN
        RAISE EXCEPTION 'Il reste % section(s) référençant l''adhérent 125', count_sections;
    END IF;
END $$;

-- Vérification des listes de diffusion
DO $$
DECLARE
    count_listes INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_listes FROM gestion_listediffusion_adherents WHERE adherent_id = 125;
    IF count_listes > 0 THEN
        RAISE EXCEPTION 'Il reste % liste(s) de diffusion référençant l''adhérent 125', count_listes;
    END IF;
END $$;

-- Supprimer l'adhérent 125
DELETE FROM gestion_adherent WHERE id = 125;

COMMIT;

-- ============================================
-- VÉRIFICATIONS POST-FUSION
-- ============================================

-- Afficher un résumé des données transférées
SELECT 
    'Séances dirigées' as type,
    COUNT(*) as nombre
FROM gestion_seance 
WHERE directeur_plongee_id = 58
UNION ALL
SELECT 
    'Palanquées encadrées' as type,
    COUNT(*) as nombre
FROM gestion_palanquee 
WHERE encadrant_id = 58
UNION ALL
SELECT 
    'Inscriptions aux séances' as type,
    COUNT(*) as nombre
FROM gestion_inscriptionseance 
WHERE personne_id = 58
UNION ALL
SELECT 
    'Palanquées en tant qu''élève' as type,
    COUNT(*) as nombre
FROM gestion_palanqueeleve 
WHERE eleve_id = 58
UNION ALL
SELECT 
    'Évaluations reçues' as type,
    COUNT(*) as nombre
FROM gestion_evaluation 
WHERE eleve_id = 58
UNION ALL
SELECT 
    'Évaluations d''exercices reçues' as type,
    COUNT(*) as nombre
FROM gestion_evaluationexercice 
WHERE eleve_id = 58
UNION ALL
SELECT 
    'Évaluations d''exercices données' as type,
    COUNT(*) as nombre
FROM gestion_evaluationexercice 
WHERE encadrant_id = 58;

