# Guide de Déploiement - Aquadémie Paris Plongée

Ce guide détaille les étapes pour déployer l'application Django Aquadémie Paris Plongée sur des serveurs Linux et Windows.

## 📋 Table des matières

- [Prérequis](#prérequis)
- [Déploiement Linux (Ubuntu/Debian)](#déploiement-linux-ubuntudebian)
- [Déploiement Windows Server](#déploiement-windows-server)
- [Configuration de la base de données](#configuration-de-la-base-de-données)
- [Configuration du serveur web](#configuration-du-serveur-web)
- [Sécurité](#sécurité)
- [Maintenance](#maintenance)
- [Dépannage](#dépannage)

## 🎯 Prérequis

### Matériel recommandé
- **CPU** : 2 cœurs minimum
- **RAM** : 4 GB minimum
- **Stockage** : 20 GB minimum
- **Réseau** : Connexion internet stable

### Logiciels requis
- Python 3.8+
- PostgreSQL 12+ (recommandé) ou SQLite (développement)
- Nginx ou Apache
- Git

---

## 🐧 Déploiement Linux (Ubuntu/Debian)

### 1. Préparation du serveur

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des paquets de base
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Installation de PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Installation de Nginx
sudo apt install -y nginx

# Installation des dépendances système
sudo apt install -y build-essential libpq-dev python3-dev
```

### 2. Configuration de PostgreSQL

```bash
# Accès à PostgreSQL
sudo -u postgres psql

# Création de la base de données et de l'utilisateur
CREATE DATABASE aquademie_db;
CREATE USER aquademie_user WITH PASSWORD 'madjer5915';
GRANT ALL PRIVILEGES ON DATABASE aquademie_db TO aquademie_user;
ALTER USER aquademie_user CREATEDB;
\q
```

### 3. Déploiement de l'application

```bash
# Création du répertoire de l'application
sudo mkdir -p /var/www/aquademie
sudo chown $USER:$USER /var/www/aquademie
cd /var/www/aquademie

# Clonage du projet
git clone https://github.com/abissolah/aquademie-technique.git .

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt

# Installation de Gunicorn
pip install gunicorn
```

### 4. Configuration Django

```bash
# Création du fichier de configuration local
cp club_plongee/settings.py club_plongee/settings_local.py
```

Éditez `club_plongee/settings_local.py` :

```python
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'votre_cle_secrete_tres_longue_et_complexe'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['votre-domaine.com', 'www.votre-domaine.com', 'IP_DU_SERVEUR']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'aquademie_db',
        'USER': 'aquademie_user',
        'PASSWORD': 'madjer5915',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS settings (à activer après configuration SSL)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
```

### 5. Configuration de l'application

```bash
# Variables d'environnement
export DJANGO_SETTINGS_MODULE=club_plongee.settings_local

# Migrations de la base de données
python manage.py migrate

# Création d'un superutilisateur
python manage.py createsuperuser

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Création des données de test (optionnel)
python manage.py creer_donnees_test
```

### 6. Configuration de Gunicorn

Créez `/etc/systemd/system/aquademie.service` :

```ini
[Unit]
Description=Aquadémie Paris Plongée Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/aquademie
Environment="PATH=/var/www/aquademie/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=club_plongee.settings_local"
ExecStart=/var/www/aquademie/venv/bin/gunicorn --workers 3 --bind unix:/var/www/aquademie/aquademie.sock club_plongee.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 7. Configuration de Nginx

Créez `/etc/nginx/sites-available/aquademie` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/aquademie;
    }
    
    location /media/ {
        root /var/www/aquademie;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/aquademie/aquademie.sock;
    }
}
```

### 8. Activation des services

```bash
# Permissions
sudo chown -R www-data:www-data /var/www/aquademie
sudo chmod -R 755 /var/www/aquademie

# Activation du service Gunicorn
sudo systemctl start aquademie
sudo systemctl enable aquademie

# Activation du site Nginx
sudo ln -s /etc/nginx/sites-available/aquademie /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Vérification des services
sudo systemctl status aquademie
sudo systemctl status nginx
```

---

## 🪟 Déploiement Windows Server

### 1. Préparation du serveur

```powershell
# Installation de Chocolatey (gestionnaire de paquets)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Installation des paquets
choco install python git postgresql nginx -y

# Redémarrage pour appliquer les changements
Restart-Computer -Force
```

### 2. Configuration de PostgreSQL

```powershell
# Accès à PostgreSQL
psql -U postgres

# Création de la base de données et de l'utilisateur
CREATE DATABASE aquademie_db;
CREATE USER aquademie_user WITH PASSWORD 'votre_mot_de_passe_securise';
GRANT ALL PRIVILEGES ON DATABASE aquademie_db TO aquademie_user;
ALTER USER aquademie_user CREATEDB;
\q
```

### 3. Déploiement de l'application

```powershell
# Création du répertoire
New-Item -ItemType Directory -Path "C:\inetpub\aquademie" -Force
Set-Location "C:\inetpub\aquademie"

# Clonage du projet
git clone https://github.com/abissolah/aquademie-technique.git .

# Création de l'environnement virtuel
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installation des dépendances
pip install -r requirements.txt

# Installation de Waitress (serveur WSGI pour Windows)
pip install waitress
```

### 4. Configuration Django

```powershell
# Copie du fichier de configuration
Copy-Item "club_plongee\settings.py" "club_plongee\settings_local.py"
```

Éditez `club_plongee/settings_local.py` (même contenu que pour Linux).

### 5. Configuration de l'application

```powershell
# Variables d'environnement
$env:DJANGO_SETTINGS_MODULE = "club_plongee.settings_local"

# Migrations
python manage.py migrate

# Création du superutilisateur
python manage.py createsuperuser

# Collecte des fichiers statiques
python manage.py collectstatic --noinput
```

### 6. Configuration du service Windows

Créez `C:\inetpub\aquademie\start_server.py` :

```python
import os
import sys
from waitress import serve
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'club_plongee.settings_local')
application = get_wsgi_application()

if __name__ == '__main__':
    serve(application, host='0.0.0.0', port=8000)
```

### 7. Configuration du service Windows

```powershell
# Création du service
New-Service -Name "Aquademie" -BinaryPathName "C:\inetpub\aquademie\venv\Scripts\python.exe C:\inetpub\aquademie\start_server.py" -DisplayName "Aquadémie Paris Plongée" -StartupType Automatic

# Démarrage du service
Start-Service -Name "Aquademie"
```

### 8. Configuration d'IIS (Alternative à Nginx)

```powershell
# Installation d'IIS
Install-WindowsFeature -Name Web-Server -IncludeManagementTools

# Installation du module URL Rewrite
Invoke-WebRequest -Uri "https://download.microsoft.com/download/D/D/E/DDE57C6C-62D9-4028-8E81-5D28A9B2A8C9/urlrewrite2.exe" -OutFile "urlrewrite2.exe"
Start-Process -FilePath "urlrewrite2.exe" -ArgumentList "/quiet" -Wait

# Configuration du site web dans IIS Manager
```

---

## 🗄️ Configuration de la base de données

### PostgreSQL (Recommandé pour la production)

```sql
-- Optimisations pour la production
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Redémarrage de PostgreSQL
SELECT pg_reload_conf();
```

### Sauvegarde automatique

```bash
# Script de sauvegarde (Linux)
#!/bin/bash
BACKUP_DIR="/var/backups/aquademie"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump aquademie_db > $BACKUP_DIR/aquademie_$DATE.sql
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

---

## 🌐 Configuration du serveur web

### Nginx (Linux)

```nginx
# Configuration optimisée
upstream aquademie {
    server unix:/var/www/aquademie/aquademie.sock;
}

server {
    listen 80;
    server_name votre-domaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;

    # Sécurité SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    location /static/ {
        alias /var/www/aquademie/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/aquademie/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://aquademie;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Certificat SSL avec Let's Encrypt

```bash
# Installation de Certbot
sudo apt install certbot python3-certbot-nginx

# Obtention du certificat
sudo certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Renouvellement automatique
sudo crontab -e
# Ajouter : 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🔒 Sécurité

### Configuration du pare-feu

```bash
# Linux (UFW)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Windows (PowerShell)
New-NetFirewallRule -DisplayName "HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
```

### Sécurité Django

```python
# settings_local.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Surveillance des logs

```bash
# Monitoring des logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
journalctl -u aquademie -f
```

---

## 🔧 Maintenance

### Mise à jour de l'application

```bash
# Sauvegarde
pg_dump aquademie_db > backup_$(date +%Y%m%d).sql

# Mise à jour du code
git pull origin master

# Mise à jour des dépendances
source venv/bin/activate
pip install -r requirements.txt

# Migrations
python manage.py migrate

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Redémarrage des services
sudo systemctl restart aquademie
sudo systemctl restart nginx
```

### Surveillance des performances

```bash
# Monitoring système
htop
df -h
free -h

# Monitoring PostgreSQL
psql -d aquademie_db -c "SELECT * FROM pg_stat_activity;"
```

---

## 🚨 Dépannage

### Problèmes courants

#### 1. Erreur 502 Bad Gateway
```bash
# Vérifier le service Gunicorn
sudo systemctl status aquademie
sudo journalctl -u aquademie -n 50

# Vérifier les permissions
sudo chown -R www-data:www-data /var/www/aquademie
```

#### 2. Erreur de base de données
```bash
# Vérifier la connexion PostgreSQL
sudo -u postgres psql -d aquademie_db

# Vérifier les logs PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. Fichiers statiques non trouvés
```bash
# Recollecter les fichiers statiques
python manage.py collectstatic --noinput --clear

# Vérifier les permissions
sudo chmod -R 755 /var/www/aquademie/staticfiles
```

#### 4. Erreur de migration
```bash
# Vérifier l'état des migrations
python manage.py showmigrations

# Appliquer les migrations manquantes
python manage.py migrate --fake-initial
```

### Logs utiles

```bash
# Logs Nginx
sudo tail -f /var/log/nginx/error.log

# Logs Django
sudo journalctl -u aquademie -f

# Logs système
sudo dmesg | tail
```

---

## 📞 Support

En cas de problème :

1. **Vérifiez les logs** : Commencez toujours par examiner les logs
2. **Documentation Django** : https://docs.djangoproject.com/
3. **Documentation Nginx** : https://nginx.org/en/docs/
4. **Documentation PostgreSQL** : https://www.postgresql.org/docs/

---

## 📝 Notes importantes

- **Sauvegardes** : Effectuez des sauvegardes régulières de la base de données
- **Mises à jour** : Maintenez le système à jour pour la sécurité
- **Monitoring** : Surveillez les performances et l'espace disque
- **Sécurité** : Changez régulièrement les mots de passe et clés secrètes
- **Tests** : Testez les mises à jour en environnement de développement

---

*Dernière mise à jour : $(date)* 