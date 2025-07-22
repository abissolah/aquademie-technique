# Configuration Email - Aquadémie Paris Plongée

## 📧 Configuration SMTP

### 1. Configuration dans `settings.py`

Modifiez les paramètres suivants dans `club_plongee/settings.py` :

```python
# Configuration Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Votre serveur SMTP
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@gmail.com'  # Votre adresse email
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe-app'  # Votre mot de passe d'application
DEFAULT_FROM_EMAIL = 'Aquadémie Paris Plongée <votre-email@gmail.com>'

# Adresses en copie par défaut
EMAIL_CC_DEFAULT = [
    'admin@aquademie-paris-plongee.fr',  # Adresse admin
    'responsable@aquademie-paris-plongee.fr',  # Autres adresses
]

# Configuration du site
SITE_NAME = 'Aquadémie Paris Plongée'
SITE_URL = 'https://votre-domaine.com'  # URL de production
```

### 2. Configuration Gmail

#### Étape 1 : Activer l'authentification à 2 facteurs
1. Allez dans les paramètres de votre compte Google
2. Sécurité → Authentification à 2 facteurs → Activer

#### Étape 2 : Créer un mot de passe d'application
1. Sécurité → Mots de passe d'application
2. Sélectionnez "Application" → "Autre (nom personnalisé)"
3. Nommez-le "Aquadémie Paris Plongée"
4. Copiez le mot de passe généré (16 caractères)

#### Étape 3 : Configurer les paramètres
```python
EMAIL_HOST_USER = 'votre-email@gmail.com'
EMAIL_HOST_PASSWORD = 'mot-de-passe-app-16-caracteres'
```

### 3. Configuration Outlook/Hotmail

```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@outlook.com'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe'
```

### 4. Configuration OVH

```python
EMAIL_HOST = 'ssl0.ovh.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@votre-domaine.com'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe'
```

## 🔧 Configuration des adresses en copie

### Adresses par défaut
Modifiez `EMAIL_CC_DEFAULT` dans `settings.py` :

```python
EMAIL_CC_DEFAULT = [
    'admin@aquademie-paris-plongee.fr',
    'responsable@aquademie-paris-plongee.fr',
    'directeur@aquademie-paris-plongee.fr',
]
```

### Adresses personnalisées
Vous pouvez également envoyer des emails avec des adresses CC personnalisées en utilisant la fonction `envoyer_lien_evaluation_avec_cc()`.

## 📋 Test de la configuration

### 1. Test en développement
```bash
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Test simple
send_mail(
    'Test Email',
    'Ceci est un test.',
    settings.DEFAULT_FROM_EMAIL,
    ['destinataire@example.com'],
    fail_silently=False,
)
```

### 2. Test de la fonction d'envoi
```python
from gestion.utils import envoyer_lien_evaluation
from gestion.models import LienEvaluation

# Récupérer un lien d'évaluation
lien = LienEvaluation.objects.first()
success, message = envoyer_lien_evaluation(lien)
print(f"Succès: {success}, Message: {message}")
```

## 🚨 Sécurité

### Variables d'environnement (Recommandé)
Pour la production, utilisez des variables d'environnement :

```python
import os

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
```

### Fichier .env
Créez un fichier `.env` à la racine du projet :

```env
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
EMAIL_CC_DEFAULT=admin@aquademie-paris-plongee.fr,responsable@aquademie-paris-plongee.fr
SITE_URL=https://votre-domaine.com
```

Puis installez `python-dotenv` :
```bash
pip install python-dotenv
```

Et ajoutez dans `settings.py` :
```python
from dotenv import load_dotenv
load_dotenv()
```

## 📧 Template d'email

Le template d'email se trouve dans `templates/gestion/email_lien_evaluation.html`.

### Personnalisation
Vous pouvez modifier :
- Le design (CSS)
- Le contenu du message
- Les informations affichées
- Le style des boutons

### Variables disponibles
- `{{ seance }}` : Objet séance
- `{{ encadrant }}` : Objet encadrant
- `{{ lien }}` : Objet lien d'évaluation
- `{{ lien_complet }}` : URL complète du lien
- `{{ site_name }}` : Nom du site

## 🔄 Fonctionnalités

### Envoi automatique
- Lien d'évaluation envoyé à l'encadrant
- Copie automatique aux adresses configurées
- Email HTML avec design professionnel
- Instructions d'utilisation incluses

### Gestion des erreurs
- Vérification de l'adresse email de l'encadrant
- Messages d'erreur explicites
- Logs d'erreur pour le débogage

### Sécurité
- Validation des adresses email
- Protection contre les injections
- Authentification SMTP sécurisée

## 📞 Support

En cas de problème :
1. Vérifiez la configuration SMTP
2. Testez avec un email simple
3. Consultez les logs Django
4. Contactez l'administrateur système 