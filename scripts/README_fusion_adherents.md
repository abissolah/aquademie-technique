# Script de fusion d'adhérents

## Description

Ce script permet de fusionner deux adhérents en transférant toutes les données de l'adhérent 125 vers l'adhérent 58, puis en supprimant l'adhérent 125.

## ⚠️ AVERTISSEMENT IMPORTANT

**Ce script modifie définitivement la base de données. Il est CRUCIAL de :**

1. **Faire une sauvegarde complète de la base de données avant d'exécuter le script**
2. **Tester le script sur une copie de la base de données de production si possible**
3. **Vérifier que les IDs 58 et 125 correspondent bien aux adhérents à fusionner**

## Données transférées

Le script transfère toutes les données suivantes de l'adhérent 125 vers l'adhérent 58 :

- **Séances** : Directeur de plongée
- **Palanquées** : Encadrant
- **Inscriptions** : Inscriptions aux séances
- **Palanquées élèves** : Participation en tant qu'élève
- **Évaluations** : Évaluations reçues
- **Évaluations d'exercices** : 
  - Évaluations reçues (en tant qu'élève)
  - Évaluations données (en tant qu'encadrant)
- **Sections** : Sections associées (ManyToMany)
- **Listes de diffusion** : Appartenance aux listes de diffusion (ManyToMany)
- **Compte utilisateur** : Si l'adhérent 58 n'a pas de compte et que l'adhérent 125 en a un

## Gestion des doublons

Le script gère automatiquement les contraintes d'unicité en supprimant les enregistrements en double avant de transférer les données :

- Inscriptions aux séances (si l'adhérent 58 est déjà inscrit à une séance où 125 l'est aussi)
- Palanquées élèves (si l'adhérent 58 est déjà dans une palanquée où 125 l'est aussi)
- Évaluations (si l'adhérent 58 a déjà été évalué pour la même compétence dans la même palanquée)

## Utilisation

### 1. Sauvegarde de la base de données

```bash
# Exemple avec pg_dump
pg_dump -h localhost -U votre_utilisateur -d votre_base > backup_avant_fusion_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Vérification des adhérents

Avant d'exécuter le script, vérifiez que les IDs correspondent bien :

```sql
SELECT id, nom, prenom, email, statut FROM gestion_adherent WHERE id IN (58, 125);
```

### 3. Exécution du script

```bash
# Avec psql
psql -h localhost -U votre_utilisateur -d votre_base -f scripts/fusionner_adherents_58_125.sql

# Ou en se connectant d'abord à PostgreSQL
psql -h localhost -U votre_utilisateur -d votre_base
\i scripts/fusionner_adherents_58_125.sql
```

### 4. Vérification post-exécution

Le script affiche automatiquement un résumé des données transférées à la fin de l'exécution.

Vous pouvez également vérifier manuellement :

```sql
-- Vérifier que l'adhérent 125 n'existe plus
SELECT * FROM gestion_adherent WHERE id = 125;

-- Vérifier que l'adhérent 58 existe toujours
SELECT * FROM gestion_adherent WHERE id = 58;

-- Vérifier qu'il n'y a plus de références à l'adhérent 125
SELECT 'seance' as table_name, COUNT(*) as count FROM gestion_seance WHERE directeur_plongee_id = 125
UNION ALL
SELECT 'palanquee', COUNT(*) FROM gestion_palanquee WHERE encadrant_id = 125
UNION ALL
SELECT 'inscriptionseance', COUNT(*) FROM gestion_inscriptionseance WHERE personne_id = 125
UNION ALL
SELECT 'palanqueeleve', COUNT(*) FROM gestion_palanqueeleve WHERE eleve_id = 125
UNION ALL
SELECT 'evaluation', COUNT(*) FROM gestion_evaluation WHERE eleve_id = 125
UNION ALL
SELECT 'evaluationexercice', COUNT(*) FROM gestion_evaluationexercice WHERE eleve_id = 125 OR encadrant_id = 125;
```

## En cas de problème

Si vous avez fait une sauvegarde avant l'exécution, vous pouvez restaurer la base de données :

```bash
psql -h localhost -U votre_utilisateur -d votre_base < backup_avant_fusion_YYYYMMDD_HHMMSS.sql
```

## Notes

- Le script utilise une transaction (BEGIN/COMMIT) pour garantir l'intégrité des données
- Si une erreur survient, toutes les modifications seront annulées automatiquement
- Le script vérifie qu'il ne reste plus de références à l'adhérent 125 avant de le supprimer
- Si une vérification échoue, le script s'arrête et la transaction est annulée

