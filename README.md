# Application de Gestion de Club de Plongée

Une application web Django moderne pour la gestion complète d'un club de plongée, incluant la gestion des adhérents, des séances, des compétences et des évaluations.

## 🚀 Fonctionnalités

### Gestion des Adhérents
- **Informations complètes** : Nom, prénom, date de naissance, adresse, email, téléphone, photo
- **Informations de plongée** : Date de fin de validité du CACI, niveau, statut (Élève/Encadrant)
- **Niveaux supportés** : Débutant, Niveau 1-3, Initiateur 1-2, Moniteur fédéral 1-2
- **Recherche et filtrage** avancés

### Gestion des Sections et Compétences
- **Sections** : Baptême, Prépa Niveau 1-4, Niveau 3-4, Encadrant
- **Compétences** : Gestion des compétences par section
- **Groupes de compétences** : Organisation des compétences avec modalités d'évaluation

### Gestion des Séances
- **Création de séances** avec palanquée, date, section, encadrant
- **Assignation d'élèves** et de compétences
- **Précisions d'exercices** détaillées
- **Génération de fiches PDF** automatique

### Système d'Évaluation
- **Évaluation par étoiles** (0-5) pour chaque compétence
- **Liens d'évaluation publics** accessibles sans connexion
- **Interface mobile optimisée** pour les évaluations sur le terrain
- **Commentaires** optionnels pour chaque évaluation

### Interface Moderne
- **Design responsive** optimisé pour mobile et desktop
- **Interface intuitive** avec Bootstrap 5
- **Navigation fluide** avec menus déroulants
- **Animations et transitions** pour une meilleure UX

## 🛠️ Technologies Utilisées

- **Backend** : Django 5.2.4
- **Base de données** : PostgreSQL
- **Frontend** : Bootstrap 5, Font Awesome
- **Formulaires** : Django Crispy Forms
- **PDF** : ReportLab
- **Images** : Pillow

## 📋 Prérequis

- Python 3.8+
- PostgreSQL
- pip

## 🔧 Installation

### 1. Cloner le projet
```bash
git clone <url-du-repo>
cd club_plongee
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv
```

### 3. Activer l'environnement virtuel
**Windows :**
```bash
venv\Scripts\activate
```

**Linux/Mac :**
```bash
source venv/bin/activate
```

### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 5. Configurer la base de données PostgreSQL
```sql
CREATE DATABASE club_plongee_db;
CREATE USER club_plongee_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE club_plongee_db TO club_plongee_user;
```

### 6. Configurer les paramètres
Modifiez `club_plongee/settings.py` avec vos paramètres de base de données :
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'club_plongee_db',
        'USER': 'club_plongee_user',
        'PASSWORD': 'votre_mot_de_passe',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 7. Effectuer les migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 9. Collecter les fichiers statiques
```bash
python manage.py collectstatic
```

### 10. Lancer le serveur
```bash
python manage.py runserver
```

L'application sera accessible à l'adresse : http://127.0.0.1:8000/

## 📖 Utilisation

### Première configuration

1. **Accéder à l'interface d'administration** : http://127.0.0.1:8000/admin/
2. **Créer les sections** : Baptême, Prépa Niveau 1, etc.
3. **Ajouter des compétences** pour chaque section
4. **Créer des groupes de compétences** si nécessaire

### Gestion des adhérents

1. **Ajouter des adhérents** via l'interface web ou l'admin
2. **Définir leur niveau** et statut (Élève/Encadrant)
3. **Uploader une photo** (optionnel)
4. **Vérifier la validité du CACI**

### Création de séances

1. **Créer une nouvelle séance** avec les informations de base
2. **Sélectionner la section** et l'encadrant
3. **Ajouter les élèves** participants
4. **Sélectionner les compétences** à travailler
5. **Ajouter les précisions d'exercices**

### Évaluations

1. **Générer un lien d'évaluation** depuis la page de la séance
2. **Partager le lien** avec l'encadrant
3. **L'encadrant évalue** les élèves sur mobile ou desktop
4. **Consulter les résultats** dans l'application

## 🔐 Sécurité

- **Authentification requise** pour toutes les fonctionnalités
- **Liens d'évaluation sécurisés** avec tokens uniques
- **Expiration automatique** des liens d'évaluation
- **Validation des données** côté serveur et client

## 📱 Responsive Design

L'application est entièrement responsive et optimisée pour :
- **Desktop** : Interface complète avec toutes les fonctionnalités
- **Tablette** : Adaptation automatique des menus et tableaux
- **Mobile** : Interface simplifiée, boutons plus grands, évaluations optimisées

## 🎨 Personnalisation

### Couleurs et thème
Modifiez `static/css/style.css` pour personnaliser :
- Couleurs principales
- Typographie
- Animations
- Styles des composants

### Logo et branding
Remplacez les icônes Font Awesome par votre logo dans les templates.

## 🚀 Déploiement

### Production
Pour un déploiement en production :

1. **Configurer un serveur web** (Nginx, Apache)
2. **Utiliser Gunicorn** comme serveur WSGI
3. **Configurer les variables d'environnement**
4. **Sécuriser la base de données**
5. **Configurer HTTPS**

### Variables d'environnement
```bash
export SECRET_KEY="votre_clé_secrète"
export DEBUG=False
export ALLOWED_HOSTS="votre-domaine.com"
```

## 📊 Fonctionnalités Avancées

### API REST
L'application inclut des endpoints API pour :
- Récupération des compétences par section
- Intégration avec d'autres systèmes

### Export PDF
- **Fiches de séance** automatiques
- **Rapports d'évaluation** personnalisables
- **Statistiques** exportables

### Notifications
- **Alertes de validité CACI** expirant
- **Rappels de séances** programmées
- **Notifications d'évaluations** en attente

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Consulter la documentation Django
- Contacter l'équipe de développement

## 📚 Documentation

Guides détaillés dans le dossier **[documents/](documents/)** :

- [Déploiement](documents/DEPLOIEMENT.md)
- [Docker / Synology production](documents/DEPLOIEMENT_DOCKER_SYNOLOGY.md)
- [Bascule de saison](documents/BASCULE_SAISON.md)
- [Dev Windows + PostgreSQL](documents/INSTALL_DEV_WINDOWS_POSTGRES.md)

## 🔄 Mises à jour

Pour mettre à jour l'application :

```bash
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
```

---

**Développé avec ❤️ pour les clubs de plongée** 