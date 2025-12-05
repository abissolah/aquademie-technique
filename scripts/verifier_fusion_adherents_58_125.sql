-- Script de vérification avant fusion des adhérents 125 vers 58
-- Ce script permet de voir toutes les données qui seront transférées
-- Exécuter ce script AVANT le script de fusion pour vérifier les données

-- ============================================
-- VÉRIFICATION DES ADHÉRENTS
-- ============================================

SELECT 
    id,
    nom,
    prenom,
    email,
    statut,
    user_id,
    date_creation
FROM gestion_adherent 
WHERE id IN (58, 125)
ORDER BY id;

-- ============================================
-- COMPTAGE DES DONNÉES À TRANSFÉRER
-- ============================================

SELECT 
    'Séances dirigées' as type_donnee,
    COUNT(*) as nombre_125,
    (SELECT COUNT(*) FROM gestion_seance WHERE directeur_plongee_id = 58) as nombre_58
FROM gestion_seance 
WHERE directeur_plongee_id = 125

UNION ALL

SELECT 
    'Palanquées encadrées' as type_donnee,
    COUNT(*) as nombre_125,
    (SELECT COUNT(*) FROM gestion_palanquee WHERE encadrant_id = 58) as nombre_58
FROM gestion_palanquee 
WHERE encadrant_id = 125

UNION ALL

SELECT 
    'Inscriptions aux séances' as type_donnee,
    COUNT(*) as nombre_125,
    (SELECT COUNT(*) FROM gestion_inscriptionseance WHERE personne_id = 58) as nombre_58
FROM gestion_inscriptionseance 
WHERE personne_id = 125

UNION ALL

SELECT 
    'Palanquées en tant qu''élève' as type_donnee,
    COUNT(*) as nombre_125,
    (SELECT COUNT(*) FROM gestion_palanqueeleve WHERE eleve_id = 58) as nombre_58
FROM gestion_palanqueeleve 
WHERE eleve_id = 125

UNION ALL

SELECT 
    'Évaluations reçues' as type_donnee,
    COUNT(*) as nombre_125,
    (SELECT COUNT(*) FROM gestion_evaluation WHERE eleve_id = 58) as nombre_58
FROM gestion_evaluation 
WHERE eleve_id = 125

UNION ALL

SELECT 
    'Évaluations d''exercices reçues' as type_donnee,
    COUNT(*) as nombre_125,
    (SELECT COUNT(*) FROM gestion_evaluationexercice WHERE eleve_id = 58) as nombre_58
FROM gestion_evaluationexercice 
WHERE eleve_id = 125

UNION ALL

SELECT 
    'Évaluations d''exercices données' as type_donnee,
    COUNT(*) as nombre_125,
    (SELECT COUNT(*) FROM gestion_evaluationexercice WHERE encadrant_id = 58) as nombre_58
FROM gestion_evaluationexercice 
WHERE encadrant_id = 125

UNION ALL

SELECT 
    'Sections associées' as type_donnee,
    COUNT(*) as nombre_125,
    (SELECT COUNT(*) FROM gestion_adherent_sections WHERE adherent_id = 58) as nombre_58
FROM gestion_adherent_sections 
WHERE adherent_id = 125

UNION ALL

SELECT 
    'Listes de diffusion' as type_donnee,
    COUNT(*) as nombre_125,
    (SELECT COUNT(*) FROM gestion_listediffusion_adherents WHERE adherent_id = 58) as nombre_58
FROM gestion_listediffusion_adherents 
WHERE adherent_id = 125;

-- ============================================
-- DÉTECTION DES DOUBLONS POTENTIELS
-- ============================================

-- Inscriptions en double (même séance)
SELECT 
    'Inscriptions en double' as type_conflit,
    COUNT(*) as nombre_conflits
FROM gestion_inscriptionseance i125
INNER JOIN gestion_inscriptionseance i58 ON i125.seance_id = i58.seance_id
WHERE i125.personne_id = 125 AND i58.personne_id = 58

UNION ALL

-- Palanquées élèves en double (même palanquée)
SELECT 
    'Palanquées élèves en double' as type_conflit,
    COUNT(*) as nombre_conflits
FROM gestion_palanqueeleve pe125
INNER JOIN gestion_palanqueeleve pe58 ON pe125.palanquee_id = pe58.palanquee_id
WHERE pe125.eleve_id = 125 AND pe58.eleve_id = 58

UNION ALL

-- Évaluations en double (même palanquée et compétence)
SELECT 
    'Évaluations en double' as type_conflit,
    COUNT(*) as nombre_conflits
FROM gestion_evaluation e125
INNER JOIN gestion_evaluation e58 
    ON e125.palanquee_id = e58.palanquee_id 
    AND e125.competence_id = e58.competence_id
WHERE e125.eleve_id = 125 AND e58.eleve_id = 58;

-- ============================================
-- DÉTAILS DES DONNÉES À TRANSFÉRER
-- ============================================

-- Séances où l'adhérent 125 est directeur de plongée
SELECT 
    'Séances dirigées' as type,
    s.id as seance_id,
    s.date,
    l.nom as lieu
FROM gestion_seance s
JOIN gestion_lieu l ON s.lieu_id = l.id
WHERE s.directeur_plongee_id = 125
ORDER BY s.date DESC;

-- Palanquées où l'adhérent 125 est encadrant
SELECT 
    'Palanquées encadrées' as type,
    p.id as palanquee_id,
    p.nom as palanquee_nom,
    s.date as seance_date
FROM gestion_palanquee p
JOIN gestion_seance s ON p.seance_id = s.id
WHERE p.encadrant_id = 125
ORDER BY s.date DESC;

-- Inscriptions aux séances
SELECT 
    'Inscriptions' as type,
    i.id as inscription_id,
    s.date as seance_date,
    l.nom as lieu,
    i.role_pour_seance
FROM gestion_inscriptionseance i
JOIN gestion_seance s ON i.seance_id = s.id
JOIN gestion_lieu l ON s.lieu_id = l.id
WHERE i.personne_id = 125
ORDER BY s.date DESC;

-- Évaluations d'exercices données (en tant qu'encadrant)
SELECT 
    'Évaluations exercices données' as type,
    ee.id as evaluation_id,
    e.nom as exercice_nom,
    a.nom || ' ' || a.prenom as eleve_evalue,
    s.date as seance_date
FROM gestion_evaluationexercice ee
JOIN gestion_exercice e ON ee.exercice_id = e.id
JOIN gestion_adherent a ON ee.eleve_id = a.id
JOIN gestion_palanquee p ON ee.palanquee_id = p.id
JOIN gestion_seance s ON p.seance_id = s.id
WHERE ee.encadrant_id = 125
ORDER BY s.date DESC
LIMIT 20;  -- Limiter à 20 pour ne pas surcharger l'affichage

