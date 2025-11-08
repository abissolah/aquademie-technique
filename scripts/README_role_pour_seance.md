# Scripts SQL pour l'évolution "Rôle pour la séance"

Ces scripts permettent d'ajouter ou de supprimer le champ `role_pour_seance` à la table `gestion_inscriptionseance` dans PostgreSQL.

## Description de l'évolution

Cette évolution permet de passer un encadrant en élève pour une séance spécifique. Le champ `role_pour_seance` peut prendre deux valeurs :
- `'encadrant'` (par défaut) : l'encadrant reste encadrant pour cette séance
- `'eleve'` : l'encadrant est traité comme un élève pour cette séance

## Fichiers

- `add_role_pour_seance.sql` : Script pour ajouter le champ `role_pour_seance`
- `rollback_role_pour_seance.sql` : Script pour supprimer le champ (rollback)

## Utilisation

### Ajouter le champ (si la migration Django n'a pas été appliquée)

```bash
psql -U votre_utilisateur -d votre_base_de_donnees -f scripts/add_role_pour_seance.sql
```

Ou depuis psql :

```sql
\i scripts/add_role_pour_seance.sql
```

### Rollback (supprimer le champ)

⚠️ **ATTENTION** : Ce script supprime définitivement la colonne et toutes ses données.

```bash
psql -U votre_utilisateur -d votre_base_de_donnees -f scripts/rollback_role_pour_seance.sql
```

## Notes importantes

1. **Migration Django** : Si vous utilisez Django, il est recommandé d'utiliser les migrations Django (`python manage.py migrate`) plutôt que ces scripts SQL directement.

2. **Sauvegarde** : Avant d'exécuter ces scripts, assurez-vous d'avoir une sauvegarde de votre base de données.

3. **Vérification** : Les scripts incluent des requêtes de vérification pour confirmer que les modifications ont été appliquées correctement.

## Structure de la colonne ajoutée

- **Nom** : `role_pour_seance`
- **Type** : `VARCHAR(20)`
- **Valeur par défaut** : `'encadrant'`
- **Contrainte** : CHECK (role_pour_seance IN ('encadrant', 'eleve'))
- **Nullable** : NOT NULL

## Impact sur les données existantes

Toutes les inscriptions existantes auront automatiquement la valeur `'encadrant'` pour le champ `role_pour_seance`, ce qui préserve le comportement actuel.

