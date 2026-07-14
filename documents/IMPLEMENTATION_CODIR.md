# Implémentation du profil utilisateur "Codir"

## Résumé des modifications

### 1. Fonctions utilitaires ajoutées dans `gestion/utils.py`
- `is_codir(user)` : Vérifie si l'utilisateur appartient au groupe Codir
- `is_codir_eleve(user)` : Vérifie si l'utilisateur est à la fois Codir et élève
- `is_codir_encadrant(user)` : Vérifie si l'utilisateur est à la fois Codir et encadrant
- `can_access_dashboard(user)` : Vérifie si l'utilisateur peut accéder au dashboard
- `codir_only(view_func)` : Décorateur pour les vues réservées aux Codir

### 2. Modifications des vues dans `gestion/views.py`
- **Dashboard** : Accès autorisé aux utilisateurs Codir
- **AdherentListView** : Accès autorisé aux utilisateurs Codir
- **AdherentDetailView** : Accès autorisé aux utilisateurs Codir
- **EleveListView** : Accès autorisé aux utilisateurs Codir
- Ajout du contexte `is_codir`, `is_codir_eleve`, `is_codir_encadrant` dans toutes les vues

### 3. Modifications des templates
- **adherent_list.html** : 
  - Boutons cachés pour les Codir (sauf "Voir", "Communiquer", "Exporter")
  - Boutons "Modifier", "Supprimer", "Créer compte", etc. cachés
- **adherent_detail.html** :
  - Mode lecture seule pour les Codir
  - Boutons "Modifier" et "Supprimer" cachés
- **eleve_list.html** :
  - Bouton "Nouvel élève" caché pour les Codir
  - Bouton "Suivi formation" visible uniquement sur sa propre fiche pour les Codir élève
  - Boutons "Modifier" et "Supprimer" cachés pour les Codir

### 4. Commandes de gestion créées
- `create_codir_group.py` : Crée le groupe Django "Codir"
- `create_codir_test_users.py` : Crée des utilisateurs de test Codir
- `test_codir_permissions.py` : Teste les permissions Codir

## Utilisation

### 1. Créer le groupe Codir
```bash
python manage.py create_codir_group
```

### 2. Créer des utilisateurs de test
```bash
python manage.py create_codir_test_users
```

### 3. Tester les permissions
```bash
python manage.py test_codir_permissions
```

### 4. Tester les redirections
```bash
python manage.py test_codir_redirects
```

### 5. Tester les fonctions Codir (version alternative)
```bash
python manage.py test_codir_functions
```

### 6. Tester les fonctions Codir (version simplifiée)
```bash
python manage.py test_codir_simple
```

### 7. Assigner le groupe Codir à un utilisateur existant
Dans l'interface d'administration Django ou via le shell :
```python
from django.contrib.auth.models import User, Group
user = User.objects.get(username='nom_utilisateur')
codir_group = Group.objects.get(name='codir')
user.groups.add(codir_group)
```

## Fonctionnalités implémentées

✅ **Accès au dashboard** : Les utilisateurs Codir peuvent accéder au dashboard
✅ **Redirection après connexion** : Tous les utilisateurs Codir arrivent sur le dashboard (pas sur le suivi de formation pour les Codir élève)
✅ **Card adhérent** : Visible dans le dashboard
✅ **Tableaux alertes CACI** : Visibles dans le dashboard
✅ **Page adhérents** : Boutons limités (Voir, Communiquer, Exporter)
✅ **Fiche adhérent** : Mode lecture seule
✅ **Liste des élèves** : 
  - Codir encadrant : voit tous les boutons "Suivi formation"
  - Codir élève : voit le bouton "Suivi formation" uniquement sur sa propre fiche

## Notes importantes

- Le profil Codir est un **groupe Django** qui peut être combiné avec les groupes "élève" et "encadrant"
- Aucune migration de base de données n'est nécessaire
- Les permissions sont gérées via les groupes Django existants
- L'implémentation est compatible avec le système d'authentification existant
