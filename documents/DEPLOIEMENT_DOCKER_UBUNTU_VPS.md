# Déploiement production Docker sur VPS Ubuntu

Guide d’installation de l’application **Aquadémie / Suivi Tech** sur un **VPS Linux Ubuntu**, avec :

- **Docker** + **Docker Compose**
- **PostgreSQL** (conteneur)
- **Nginx hôte** + **certificat Let's Encrypt**
- Domaine : **`app-suivitech.fr`**
- IP serveur : **`145.239.78.71`**
- Base : **`aquademie_db`** / utilisateur : **`aquademie_user`**

---

## Sommaire

1. [Vue d’ensemble](#1-vue-densemble)
2. [Prérequis](#2-prérequis)
3. [Étape 1 — DNS](#3-étape-1--dns)
4. [Étape 2 — Préparer le VPS](#4-étape-2--préparer-le-vps)
5. [Étape 3 — Installer Docker](#5-étape-3--installer-docker)
6. [Étape 4 — Déployer l’application](#6-étape-4--déployer-lapplication)
7. [Étape 5 — Fichier `.env`](#7-étape-5--fichier-env)
8. [Étape 6 — Lancer la stack Docker](#8-étape-6--lancer-la-stack-docker)
9. [Étape 7 — Nginx hôte + Let's Encrypt](#9-étape-7--nginx-hôte--lets-encrypt)
10. [Étape 8 — Pare-feu](#10-étape-8--pare-feu)
11. [Étape 9 — Superutilisateur, médias, backup](#11-étape-9--superutilisateur-médias-backup)
12. [Vérifications](#12-vérifications)
13. [Sauvegardes et mises à jour](#13-sauvegardes-et-mises-à-jour)
14. [Dépannage](#14-dépannage)

---

## 1. Vue d’ensemble

```
Navigateur
    │  https://app-suivitech.fr
    ▼
DNS  →  145.239.78.71
    ▼
VPS Ubuntu
    │  Nginx hôte (ports 80/443) + Let's Encrypt
    │  Reverse proxy → http://127.0.0.1:8080
    ▼
Docker nginx (:8080)
    ▼
Docker Django / Gunicorn (:8000)
    ▼
Docker PostgreSQL (aquademie_db)
```

**Principe** : Docker expose l’app en HTTP sur **`127.0.0.1:8080`** uniquement. Le **Nginx du système** gère HTTPS et le certificat Let's Encrypt.

---

## 2. Prérequis

| Élément | Valeur |
|---------|--------|
| OS | Ubuntu 22.04 ou 24.04 LTS |
| Accès | SSH root ou utilisateur sudo |
| Domaine | `app-suivitech.fr` (et idéalement `www.app-suivitech.fr`) |
| IP | `145.239.78.71` |
| Ports ouverts chez l’hébergeur | **80** et **443** (TCP) |
| Code source | dépôt Git ou archive du projet |

---

## 3. Étape 1 — DNS

Chez votre registrar (OVH, etc.), créez :

| Type | Nom | Cible |
|------|-----|--------|
| A | `@` (ou `app-suivitech.fr`) | `145.239.78.71` |
| A | `www` | `145.239.78.71` |

Vérification (après propagation, souvent quelques minutes à 1 h) :

```bash
dig +short app-suivitech.fr
dig +short www.app-suivitech.fr
# Attendu : 145.239.78.71
```

> Let's Encrypt exige que le domaine pointe déjà vers le serveur avant la demande de certificat.

---

## 4. Étape 2 — Préparer le VPS

Connexion :

```bash
ssh root@145.239.78.71
# ou : ssh monuser@145.239.78.71
```

Mise à jour et paquets de base :

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg lsb-release git ufw fail2ban
```

Créer un utilisateur de déploiement (recommandé si vous êtes en root) :

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
```

Répertoire d’installation :

```bash
sudo mkdir -p /opt/aquademie
sudo chown "$USER:$USER" /opt/aquademie
```

---

## 5. Étape 3 — Installer Docker

### 5.1 Docker Engine (méthode officielle)

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 5.2 Droits utilisateur

```bash
sudo usermod -aG docker "$USER"
# Se déconnecter / reconnecter SSH pour prendre en compte le groupe docker
```

### 5.3 Vérifier

```bash
docker --version
docker compose version
sudo systemctl enable --now docker
sudo systemctl status docker --no-pager
```

> Sur ce VPS, utilisez **`docker compose`** (plugin officiel).  
> Si seul `docker-compose` (v1) est disponible, remplacez `docker compose` par `docker-compose` dans les commandes.

---

## 6. Étape 4 — Déployer l’application

### 6.1 Récupérer le code

**Option A — Git :**

```bash
cd /opt/aquademie
git clone <URL_DU_DEPOT> .
# ou clone dans un sous-dossier puis cd
```

**Option B — Archive scp depuis votre PC :**

```bash
# Sur votre PC
scp -r ./rapports_moniteurs deploy@145.239.78.71:/opt/aquademie/
```

Sur le serveur, placez-vous à la racine du projet (là où se trouvent `Dockerfile` et `docker-compose.prod.yml`) :

```bash
cd /opt/aquademie
ls Dockerfile docker-compose.prod.yml
```

### 6.2 Vérifier les fichiers Docker

| Fichier | Rôle |
|---------|------|
| `Dockerfile` | Image Python + dépendances |
| `docker-compose.prod.yml` | Stack prod : `db` + `web` + `nginx` |
| `docker/entrypoint.sh` | wait_for_db, migrate, collectstatic, Gunicorn |
| `docker/nginx/nginx.conf` | Nginx interne Docker |
| `.env` | Secrets et configuration (à créer) |

---

## 7. Étape 5 — Fichier `.env`

```bash
cd /opt/aquademie
cp .env.example .env
nano .env
```

Contenu minimal recommandé :

```env
# --- Django ---
DJANGO_SECRET_KEY=GENERER_UNE_CLE_LONGUE_ALEATOIRE
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=app-suivitech.fr,www.app-suivitech.fr,145.239.78.71
DJANGO_CSRF_TRUSTED_ORIGINS=https://app-suivitech.fr,https://www.app-suivitech.fr
DJANGO_SITE_URL=https://app-suivitech.fr
DJANGO_USE_WHITENOISE=True
DJANGO_BEHIND_PROXY=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True

# --- PostgreSQL ---
POSTGRES_DB=aquademie_db
POSTGRES_USER=aquademie_user
POSTGRES_PASSWORD=MOT_DE_PASSE_FORT_A_CHANGER
POSTGRES_HOST=db
POSTGRES_PORT=5432

# --- Port Docker (Nginx hôte → ce port) ---
WEB_PUBLISHED_PORT=8080

# --- Gunicorn ---
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120
DB_WAIT_TIMEOUT=60

# --- Email (à adapter) ---
EMAIL_HOST=ssl0.ovh.net
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=contact@app-suivitech.fr
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=Suivi Tech <contact@app-suivitech.fr>
EMAIL_CC_DEFAULT=admin@app-suivitech.fr

# --- Hello Asso (optionnel) ---
HELLO_ASSO_URL=
HELLO_ASSO_WEBHOOK_SECRET=
```

Générer une `DJANGO_SECRET_KEY` :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Sécuriser le fichier :

```bash
chmod 600 .env
```

**Points critiques :**

- `POSTGRES_HOST=db` (nom du service Docker, **pas** l’IP du VPS)
- `DJANGO_BEHIND_PROXY=True` (HTTPS terminé par Nginx hôte)
- `DJANGO_CSRF_TRUSTED_ORIGINS` en **`https://`** avec le domaine exact

---

## 8. Étape 6 — Lancer la stack Docker

### 8.1 Bind localhost uniquement (recommandé)

Pour que l’app Docker ne soit pas exposée directement sur Internet (seul Nginx hôte doit l’être), éditez temporairement le mapping de port **ou** publiez ainsi.

Dans `docker-compose.prod.yml`, le service `nginx` utilise :

```yaml
ports:
  - "${WEB_PUBLISHED_PORT:-80}:80"
```

Sur le VPS, forcez l’écoute locale en lançant avec une surcharge, **ou** modifiez la ligne ports en :

```yaml
ports:
  - "127.0.0.1:${WEB_PUBLISHED_PORT:-8080}:80"
```

Ainsi Docker n’écoute que sur `127.0.0.1:8080`.

### 8.2 Build et démarrage

```bash
cd /opt/aquademie
docker compose -f docker-compose.prod.yml up -d --build
```

### 8.3 Vérifier

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f web
```

Attendu :

- `db` : **healthy**
- `web` : « Base de données disponible », migrations OK, Gunicorn démarré
- `nginx` : Up
- Test local : `curl -I http://127.0.0.1:8080/` → réponse HTTP (200/302)

Créer un compte admin :

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## 9. Étape 7 — Nginx hôte + Let's Encrypt

### 9.1 Installer Nginx et Certbot

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo systemctl enable --now nginx
```

### 9.2 Configuration reverse proxy

```bash
sudo nano /etc/nginx/sites-available/app-suivitech.fr
```

Contenu :

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name app-suivitech.fr www.app-suivitech.fr;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 60s;
    }
}
```

Activer le site :

```bash
sudo ln -sf /etc/nginx/sites-available/app-suivitech.fr /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Test HTTP :

```bash
curl -I http://app-suivitech.fr/
curl -I http://145.239.78.71/
```

### 9.3 Certificat Let's Encrypt

```bash
sudo certbot --nginx -d app-suivitech.fr -d www.app-suivitech.fr
```

Suivre les invites (email, acceptation CGU). Certbot modifie la config Nginx pour HTTPS et la redirection HTTP → HTTPS.

Renouvellement automatique (déjà en timer en général) :

```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

### 9.4 Vérifier HTTPS

```bash
curl -I https://app-suivitech.fr/
```

Ouvrir dans le navigateur : `https://app-suivitech.fr/` et `https://app-suivitech.fr/admin/`

---

## 10. Étape 8 — Pare-feu

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

**Ne pas** ouvrir `5432` (PostgreSQL) ni `8080` vers Internet.

---

## 11. Étape 9 — Superutilisateur, médias, backup

### 11.1 Créer un accès SFTP pour transférer le backup

Si vous voulez déposer facilement un fichier de backup sur le VPS avant restauration, vous pouvez créer un utilisateur SFTP dédié.

### 11.1.1 Créer un utilisateur dédié

```bash
sudo adduser backupadmin
```

Choisissez un mot de passe fort, puis créez un répertoire de dépôt :

```bash
sudo mkdir -p /opt/transferts
sudo chown backupadmin:backupadmin /opt/transferts
chmod 750 /opt/transferts
```

### 11.1.2 Vérifier que le service SSH est actif

```bash
sudo systemctl status ssh --no-pager
```

Si besoin :

```bash
sudo systemctl enable --now ssh
```

### 11.1.3 Se connecter en SFTP

Depuis un client SFTP comme WinSCP ou FileZilla :

| Paramètre | Valeur |
|-----------|--------|
| Hôte | `145.239.78.71` |
| Protocole | `SFTP` |
| Port | `22` |
| Utilisateur | `backupadmin` |
| Mot de passe | celui défini à la création |

Vous pouvez alors transférer votre fichier, par exemple vers :

`/opt/transferts/aquademie_db.backup`

En ligne de commande, vous pouvez aussi utiliser `scp` :

```bash
scp aquademie_db.backup backupadmin@145.239.78.71:/opt/transferts/
```

Puis vérifier sur le VPS :

```bash
ls -lh /opt/transferts/
```

> Variante plus sécurisée : remplacer le mot de passe par une authentification par clé SSH. Ce n'est pas obligatoire pour un transfert ponctuel, mais c'est recommandé en production.

### 11.2 Restaurer une base existante (optionnel)

Si vous avez un dump déjà transféré sur le VPS :

```bash
# Copier le dump dans le conteneur
docker cp /opt/transferts/aquademie_db.backup "$(docker compose -f docker-compose.prod.yml ps -q db)":/tmp/aquademie_db.backup

# Dump texte (.sql) :
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U aquademie_user -d aquademie_db < /opt/transferts/aquademie_db.backup

# Dump custom (pg_dump -Fc) :
docker compose -f docker-compose.prod.yml exec db \
  pg_restore -U aquademie_user -d aquademie_db --no-owner --role=aquademie_user /tmp/aquademie_db.backup
```

Si après restauration Django tente de réappliquer des migrations déjà présentes dans le schéma :

```bash
docker compose -f docker-compose.prod.yml run --rm --no-deps --entrypoint python web manage.py migrate gestion 0028 --fake
docker compose -f docker-compose.prod.yml run --rm --no-deps --entrypoint python web manage.py migrate
```

### 11.3 Copier les médias

Prérequis : le fichier `media.zip` a été déposé via SFTP dans `/opt/transferts/` (étape 11.1).

```bash
cd /opt/aquademie/aquademie-technique

# 1. Dézipper dans un dossier temporaire
sudo apt install -y unzip
rm -rf /opt/transferts/media_extract
mkdir -p /opt/transferts/media_extract
unzip -o /opt/transferts/media.zip -d /opt/transferts/media_extract

# 2. Voir la structure (utile si le zip contient un dossier media/ racine)
find /opt/transferts/media_extract -maxdepth 2 -type d

# 3. Copier vers le volume Docker
# Cas A — le zip contient directement photos_adherents/, caci/, etc. :
docker cp /opt/transferts/media_extract/. \
  "$(docker compose -f docker-compose.prod.yml ps -q web)":/app/media/

# Cas B — le zip contient un sous-dossier media/ :
# docker cp /opt/transferts/media_extract/media/. \
#   "$(docker compose -f docker-compose.prod.yml ps -q web)":/app/media/

# 4. Permissions + vérification
docker compose -f docker-compose.prod.yml exec web chmod -R u+rwX,g+rX,o+rX /app/media
docker compose -f docker-compose.prod.yml exec web ls -la /app/media
docker compose -f docker-compose.prod.yml exec web du -sh /app/media
```

Vous devez voir directement sous `/app/media/` des dossiers du type `photos_adherents`, `caci`, `uploads`, etc.

**Si vous voyez `/app/media/media/`** (un niveau de trop) :

```bash
docker compose -f docker-compose.prod.yml exec web sh -c \
  "mv /app/media/media/* /app/media/ && rmdir /app/media/media && chmod -R u+rwX,g+rX,o+rX /app/media"
```

Test rapide :

```bash
curl -I -H "Host: app-suivitech.fr" \
  http://127.0.0.1:8080/media/photos_adherents/IMG_0808.jpeg
```

(Adaptez le nom de fichier à un fichier réellement présent.)

### 11.4 Collectstatic (déjà fait au démarrage)

En cas de besoin :

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## 12. Vérifications

| Contrôle | Commande / URL |
|----------|----------------|
| Conteneurs | `docker compose -f docker-compose.prod.yml ps` |
| App locale | `curl -I http://127.0.0.1:8080/` |
| HTTPS | `https://app-suivitech.fr/` |
| Admin | `https://app-suivitech.fr/admin/` |
| Login CSRF | Connexion admin OK |
| Médias | Une photo `/media/photos_adherents/...` en 200 |
| BDD | `docker compose -f docker-compose.prod.yml exec db psql -U aquademie_user -d aquademie_db -c '\dt'` |

---

## 13. Sauvegardes et mises à jour

### 13.1 Sauvegarde PostgreSQL

```bash
cd /opt/aquademie
mkdir -p /opt/backups
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U aquademie_user -d aquademie_db -F c \
  > /opt/backups/aquademie_db_$(date +%Y%m%d_%H%M).backup
```

### 13.2 Sauvegarde médias

```bash
docker run --rm -v aquademie_media_data:/data -v /opt/backups:/backup alpine \
  tar czf /backup/media_$(date +%Y%m%d).tar.gz -C /data .
```

> Le nom exact du volume peut varier (`docker volume ls | grep media`).

### 13.3 Mise à jour de l’application

```bash
cd /opt/aquademie
git pull   # ou recopier les fichiers
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f web
```

---

## 14. Dépannage

### Base indisponible (`wait_for_db`)

- Vérifier `POSTGRES_HOST=db` dans `.env`
- Vérifier `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`
- Logs : `docker compose -f docker-compose.prod.yml logs db`

### Erreur CSRF 403

- `DJANGO_CSRF_TRUSTED_ORIGINS=https://app-suivitech.fr,https://www.app-suivitech.fr`
- `DJANGO_BEHIND_PROXY=True`
- Nginx hôte doit envoyer `X-Forwarded-Proto $scheme`
- Recréer web après modif `.env` :  
  `docker compose -f docker-compose.prod.yml up -d --force-recreate web`

### Médias en 404

- Fichiers dans le **bon** projet Docker (`docker compose ps`)
- Contenu sous `/app/media/` (pas `/app/media/media/`)
- Accents : noms de fichiers UTF-8 cohérents avec la BDD

### Certificat Let's Encrypt échoue

- DNS A → `145.239.78.71` propagé
- Ports 80/443 ouverts (hébergeur + `ufw`)
- Aucun autre service n’occupe le port 80

### Migration « column already exists » après restore

```bash
docker compose -f docker-compose.prod.yml run --rm --no-deps --entrypoint python web manage.py migrate gestion 0028 --fake
docker compose -f docker-compose.prod.yml run --rm --no-deps --entrypoint python web manage.py migrate
```

---

## Récapitulatif des paramètres de ce déploiement

| Paramètre | Valeur |
|-----------|--------|
| Domaine | `app-suivitech.fr` |
| IP | `145.239.78.71` |
| Base PostgreSQL | `aquademie_db` |
| Utilisateur PostgreSQL | `aquademie_user` |
| Host PostgreSQL (Docker) | `db` |
| Port app Docker | `127.0.0.1:8080` |
| HTTPS | Nginx hôte + Certbot Let's Encrypt |
| Répertoire projet | `/opt/aquademie` |

---

## Checklist finale

1. DNS A → `145.239.78.71`
2. Ubuntu à jour, Docker + Compose installés
3. Projet dans `/opt/aquademie` avec `.env` correct
4. `docker compose -f docker-compose.prod.yml up -d --build`
5. Nginx hôte → `127.0.0.1:8080` + en-têtes `X-Forwarded-*`
6. `certbot --nginx -d app-suivitech.fr -d www.app-suivitech.fr`
7. `ufw` : SSH + 80 + 443 uniquement
8. Superuser créé, médias copiés, sauvegarde planifiée
