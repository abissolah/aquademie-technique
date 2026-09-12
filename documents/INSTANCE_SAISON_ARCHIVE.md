# Instance archive saison 2025-2026 (sans bascule)

Ce document décrit comment **héberger une deuxième instance** de l'application sur le **même VPS**, accessible via un sous-domaine dédié (ex. `https://2025.app-suivitech.fr`), en **conservant la base de données de la saison écoulée** — **sans** exécuter `basculer_saison`.

Contexte cible : **VPS Ubuntu** (`145.239.78.71`), Docker Compose, Nginx hôte + Let's Encrypt.

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Prérequis](#2-prérequis)
3. [Étape 1 — DNS](#3-étape-1--dns)
4. [Étape 2 — Préparer le répertoire archive](#4-étape-2--préparer-le-répertoire-archive)
5. [Étape 3 — Fichier `.env` de l'instance archive](#5-étape-3--fichier-env-de-linstance-archive)
6. [Étape 4 — Lancer la stack Docker (port isolé)](#6-étape-4--lancer-la-stack-docker-port-isolé)
7. [Étape 5 — Restaurer la base de données](#7-étape-5--restaurer-la-base-de-données)
8. [Étape 6 — Restaurer les fichiers media](#8-étape-6--restaurer-les-fichiers-media)
9. [Étape 7 — Nginx hôte + certificat HTTPS](#9-étape-7--nginx-hôte--certificat-https)
10. [Vérifications finales](#10-vérifications-finales)
11. [Exploitation au quotidien](#11-exploitation-au-quotidien)
12. [Dépannage](#12-dépannage)

---

## 1. Vue d'ensemble

Deux instances **indépendantes** tournent en parallèle sur le même serveur :

```
Navigateur
    │
    ├── https://app-suivitech.fr          → Nginx hôte :8080 → stack « courante » (2026-2027)
    │
    └── https://2025.app-suivitech.fr     → Nginx hôte :8081 → stack « archive » (2025-2026)
```

| Élément | Instance courante | Instance archive |
|---------|-------------------|------------------|
| Domaine | `app-suivitech.fr` | `2025.app-suivitech.fr` |
| Répertoire | `/opt/aquademie/aquademie-technique` | `/opt/aquademie/aquademie-technique-2025` |
| Projet Compose | `aquademie-technique` (défaut) | `aquademie2025` (`COMPOSE_PROJECT_NAME`) |
| Port local Docker | `8080` | `8081` |
| Base PostgreSQL | volume propre (état actuel) | volume **séparé** (restauré depuis backup) |
| Media | volume propre | volume **séparé** (restauré depuis backup) |
| Bascule saison | appliquée (ou à appliquer) | **jamais** |

> **Point clé** : l'archive repose sur la **sauvegarde réalisée avant bascule** (cf. [BASCULE_SAISON.md](BASCULE_SAISON.md), section 2). Sans ce backup, la base « saison dernière complète » n'est plus reconstituable telle quelle.

---

## 2. Prérequis

| Élément | Valeur |
|---------|--------|
| Serveur | `145.239.78.71` |
| Instance courante | déjà opérationnelle sur `app-suivitech.fr` (:8080) |
| Backup BDD | `/opt/backups/backup_avant_bascule_YYYYMMDD_HHMM.backup` |
| Backup media | `/opt/backups/media_avant_bascule_YYYYMMDD_HHMM.tar.gz` |
| Accès | SSH root ou sudo |
| Docker | installé (cf. [DEPLOIEMENT_DOCKER_UBUNTU_VPS.md](DEPLOIEMENT_DOCKER_UBUNTU_VPS.md)) |

Vérifier que les sauvegardes existent et ne sont pas vides :

```bash
ls -lh /opt/backups/backup_avant_bascule_*.backup
ls -lh /opt/backups/media_avant_bascule_*.tar.gz
```

> Si la bascule a déjà été exécutée sur l'instance courante, **seule** cette sauvegarde d'avant bascule contient l'état complet 2025-2026 (adhérents, séances, inscriptions, etc.).

---

## 3. Étape 1 — DNS

Chez votre registrar (OVH, etc.), ajouter :

| Type | Nom | Cible |
|------|-----|--------|
| A | `2025` | `145.239.78.71` |

Vérification (après propagation) :

```bash
dig +short 2025.app-suivitech.fr
# Attendu : 145.239.78.71
```

---

## 4. Étape 2 — Préparer le répertoire archive

Cloner le dépôt dans un **second répertoire** (code identique ou commit proche de la date du backup) :

```bash
sudo mkdir -p /opt/aquademie
sudo chown "$USER:$USER" /opt/aquademie

cd /opt/aquademie
git clone https://github.com/abissolah/aquademie-technique.git aquademie-technique-2025
cd aquademie-technique-2025
```

> Vous pouvez rester sur `master` si le schéma est compatible avec le backup. En cas de doute après restauration, notez le hash Git utilisé.

Créer le fichier `.env` à partir de l'exemple :

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

---

## 5. Étape 3 — Fichier `.env` de l'instance archive

Exemple pour `/opt/aquademie/aquademie-technique-2025/.env` :

```env
# --- Django (instance archive 2025-2026) ---
DJANGO_SECRET_KEY=GENERER_UNE_CLE_DIFFERENTE_DE_LINSTANCE_COURANTE
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=2025.app-suivitech.fr,127.0.0.1,localhost,145.239.78.71
DJANGO_CSRF_TRUSTED_ORIGINS=https://2025.app-suivitech.fr
DJANGO_SITE_URL=https://2025.app-suivitech.fr
DJANGO_USE_WHITENOISE=True
DJANGO_BEHIND_PROXY=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True

# --- PostgreSQL (base isolée dans son propre volume Docker) ---
POSTGRES_DB=aquademie_db
POSTGRES_USER=aquademie_user
POSTGRES_PASSWORD=MOT_DE_PASSE_FORT_ARCHIVE
POSTGRES_HOST=db
POSTGRES_PORT=5432

# --- Port local (différent de l'instance courante :8080) ---
WEB_PUBLISHED_PORT=8081

# --- Gunicorn ---
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=120
DB_WAIT_TIMEOUT=60

# --- Email (optionnel — désactiver l'envoi réel sur l'archive) ---
EMAIL_HOST=ssl0.ovh.net
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=contact@app-suivitech.fr
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=Aquadémie archive 2025-2026 <contact@app-suivitech.fr>
EMAIL_CC_DEFAULT=

# --- Hello Asso : laisser vide ou URL 2025-2026 (pas de webhook actif recommandé) ---
HELLO_ASSO_URL=
HELLO_ASSO_WEBHOOK_SECRET=

# --- Export CACI (optionnel, dossier séparé) ---
CHEMIN_SFTP=/data/caci_export
CHEMIN_SFTP_HOST=/home/backupadmin/CACI_archive_2025
```

Points importants :

- **`DJANGO_SECRET_KEY`** : doit être **différente** de l'instance courante (sessions isolées).
- **`WEB_PUBLISHED_PORT=8081`** : obligatoire pour ne pas entrer en conflit avec `:8080`.
- **`POSTGRES_PASSWORD`** : peut être identique ou différent ; l'isolation vient surtout du **volume Docker séparé**.
- **Hello Asso** : ne pas configurer de webhook vers l'archive (évite les doubles traitements).

Générer une clé secrète :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 6. Étape 4 — Lancer la stack Docker (port isolé)

Toutes les commandes ci-dessous utilisent un **nom de projet Compose distinct** pour éviter tout conflit de conteneurs et de volumes avec l'instance courante.

```bash
cd /opt/aquademie/aquademie-technique-2025

export COMPOSE_PROJECT_NAME=aquademie2025

# Écoute localhost uniquement (recommandé) — éditer docker-compose.prod.yml si besoin :
# ports:
#   - "127.0.0.1:${WEB_PUBLISHED_PORT:-8080}:80"

docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

Contrôles :

```bash
# Test direct (127.0.0.1 doit être dans DJANGO_ALLOWED_HOSTS)
curl -I http://127.0.0.1:8081/

# Test comme le fera Nginx en production (Host = sous-domaine)
curl -I -H "Host: 2025.app-suivitech.fr" http://127.0.0.1:8081/
```

Attendu : réponse HTTP **200** ou **302** (redirection login). Une **400 Bad Request** signifie en général que `127.0.0.1` n'est pas dans `DJANGO_ALLOWED_HOSTS` — voir [§12 Dépannage](#12-dépannage).

La base est encore **vide** à ce stade : c'est normal.

Créer le dossier export CACI archive si configuré :

```bash
mkdir -p /home/backupadmin/CACI_archive_2025
```

---

## 7. Étape 5 — Restaurer la base de données

Remplacer `YYYYMMDD_HHMM` par la date réelle de votre backup.

> **Important** : ne pas utiliser `pg_restore --clean` sur une base déjà initialisée par Django (migrations au premier démarrage). Cela provoque des centaines d'erreurs (`cannot drop constraint …`, `relation already exists`, colonnes `identity`) et une restauration **incomplète**.  
> La bonne méthode : **supprimer et recréer** la base vide, puis restaurer **sans** `--clean`.

```bash
cd /opt/aquademie/aquademie-technique-2025
export COMPOSE_PROJECT_NAME=aquademie2025

# Arrêter web/nginx pour éviter des connexions pendant la restauration
docker compose -f docker-compose.prod.yml stop web nginx

# Copier le backup dans le conteneur db
docker cp /opt/backups/backup_avant_bascule_YYYYMMDD_HHMM.backup \
  "$(docker compose -f docker-compose.prod.yml ps -q db)":/tmp/restore.backup

# 1) Couper les connexions actives
docker compose -f docker-compose.prod.yml exec db \
  psql -U aquademie_user -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='aquademie_db' AND pid <> pg_backend_pid();"

# 2) Recréer une base vide (uniquement dans le volume de l'archive)
docker compose -f docker-compose.prod.yml exec db \
  psql -U aquademie_user -d postgres -c "DROP DATABASE IF EXISTS aquademie_db;"

docker compose -f docker-compose.prod.yml exec db \
  psql -U aquademie_user -d postgres -c \
  "CREATE DATABASE aquademie_db OWNER aquademie_user ENCODING 'UTF8' TEMPLATE template0;"

# 3) Restaurer SANS --clean
docker compose -f docker-compose.prod.yml exec db \
  pg_restore -U aquademie_user -d aquademie_db \
  --no-owner --role=aquademie_user /tmp/restore.backup

# Redémarrer
docker compose -f docker-compose.prod.yml up -d
```

Des **warnings** isolés en fin de `pg_restore` peuvent apparaître (droits, extensions) : ce n'est pas grave si les contrôles ci-dessous sont OK.

> L'instance courante (`:8080`) n'est **pas** impactée : vous opérez sur le volume PostgreSQL du projet `aquademie2025` uniquement.

### Migrations (après restauration)

```bash
export COMPOSE_PROJECT_NAME=aquademie2025
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations gestion | tail -20
```

Si une migration pose problème sur l'archive, documenter l'erreur et éventuellement figer le code au commit de la date du backup.

### Contrôle rapide

```bash
export COMPOSE_PROJECT_NAME=aquademie2025
docker compose -f docker-compose.prod.yml exec db \
  psql -U aquademie_user -d aquademie_db -c "
SELECT
  (SELECT COUNT(*) FROM gestion_adherent) AS adherents,
  (SELECT COUNT(*) FROM gestion_seance) AS seances,
  (SELECT COUNT(*) FROM gestion_inscriptionseance) AS inscriptions;
"
```

Les effectifs doivent correspondre à l'état **avant bascule** (adhérents et séances présents).

---

## 8. Étape 6 — Restaurer les fichiers media

```bash
cd /opt/aquademie/aquademie-technique-2025
export COMPOSE_PROJECT_NAME=aquademie2025

# Vider le volume media de l'archive
docker compose -f docker-compose.prod.yml exec web sh -c "rm -rf /app/media/*"

# Restaurer depuis l'archive tar.gz
docker compose -f docker-compose.prod.yml exec -T web \
  tar xzf - -C /app < /opt/backups/media_avant_bascule_YYYYMMDD_HHMM.tar.gz

# Si l'archive contient un sous-dossier media/ à la racine :
# docker compose -f docker-compose.prod.yml exec web sh -c \
#   "mv /app/media/media/* /app/media/ 2>/dev/null; rmdir /app/media/media 2>/dev/null; true"

docker compose -f docker-compose.prod.yml exec web chmod -R u+rwX,g+rX,o+rX /app/media
docker compose -f docker-compose.prod.yml exec web ls -la /app/media
```

Vérifier qu'un dossier `caci/` ou `photos_adherents/` est présent.

---

## 9. Étape 7 — Nginx hôte + certificat HTTPS

### 9.1 Configuration reverse proxy

```bash
sudo nano /etc/nginx/sites-available/2025.app-suivitech.fr
```

Contenu :

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name 2025.app-suivitech.fr;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8081;
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

Activer :

```bash
sudo ln -sf /etc/nginx/sites-available/2025.app-suivitech.fr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Test HTTP :

```bash
curl -I http://2025.app-suivitech.fr/
curl -I http://127.0.0.1:8081/
```

### 9.2 Certificat Let's Encrypt

```bash
sudo certbot --nginx -d 2025.app-suivitech.fr
```

Vérifier HTTPS :

```bash
curl -I https://2025.app-suivitech.fr/
```

---

## 10. Vérifications finales

- [ ] `https://2025.app-suivitech.fr/` : page d'accueil / login OK
- [ ] `https://2025.app-suivitech.fr/admin/` : connexion admin OK
- [ ] Liste adhérents : effectif cohérent avec la saison 2025-2026
- [ ] Séances et inscriptions visibles
- [ ] Photos et CACI téléchargeables (media restauré)
- [ ] `https://app-suivitech.fr/` : instance courante **inchangée**
- [ ] Les deux stacks tournent en parallèle :

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | grep -E "aquademie|8080|8081"
```

- [ ] Aucun webhook Hello Asso ne pointe vers `2025.app-suivitech.fr`

---

## 11. Exploitation au quotidien

### Commandes avec le bon projet Compose

Toujours exporter le nom de projet pour l'archive :

```bash
cd /opt/aquademie/aquademie-technique-2025
export COMPOSE_PROJECT_NAME=aquademie2025

# Logs
docker compose -f docker-compose.prod.yml logs -f web

# Redémarrer
docker compose -f docker-compose.prod.yml up -d --force-recreate web

# Mise à jour code (prudence : tester sur l'archive avant la prod)
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Instance **courante** (inchangée) :

```bash
cd /opt/aquademie/aquademie-technique
docker compose -f docker-compose.prod.yml ...
```

### Règles importantes

| Action | Instance courante | Instance archive |
|--------|-------------------|------------------|
| `basculer_saison` | oui (une fois par an) | **non, jamais** |
| Webhook Hello Asso | oui | **non** |
| Inscription publique 2026-2027 | oui | **non** (consultation seulement) |
| `git pull` + rebuild | oui, régulièrement | optionnel, avec prudence |

### Sauvegardes de l'archive

Planifier un dump périodique du volume archive (lecture seule logique) :

```bash
export COMPOSE_PROJECT_NAME=aquademie2025
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U aquademie_user -d aquademie_db -F c \
  > /opt/backups/archive_2025_$(date +%Y%m%d).backup
```

---

## 12. Dépannage

### `curl http://127.0.0.1:8081/` → 400 Bad Request

Django refuse les requêtes dont l'en-tête `Host` n'est pas listé dans `ALLOWED_HOSTS`.

Dans le `.env` de l'archive, ajouter `127.0.0.1` et `localhost` :

```env
DJANGO_ALLOWED_HOSTS=2025.app-suivitech.fr,127.0.0.1,localhost,145.239.78.71
```

Puis recréer le conteneur web :

```bash
cd /opt/aquademie/aquademie-technique-2025
export COMPOSE_PROJECT_NAME=aquademie2025
docker compose -f docker-compose.prod.yml up -d --force-recreate web
```

Alternative de test sans modifier le `.env` :

```bash
curl -I -H "Host: 2025.app-suivitech.fr" http://127.0.0.1:8081/
```

> En production, Nginx envoie `Host: 2025.app-suivitech.fr` : le site fonctionnera même si seul le sous-domaine est dans `ALLOWED_HOSTS`. `127.0.0.1` sert surtout aux tests locaux sur le VPS.

### `pg_restore` : erreurs `cannot drop constraint`, `relation already exists`, `identity column`

Cause : restauration avec `--clean` sur une base déjà créée par les migrations Django au premier `docker compose up`.

**Ce n'est pas anodin** : la base peut être dans un état incohérent (tables partiellement écrasées, données manquantes).

**Correction** : reprendre l'étape 5 avec la procédure **DROP DATABASE + CREATE DATABASE + pg_restore sans `--clean`** (cf. section 7).

Puis vérifier les effectifs :

```bash
export COMPOSE_PROJECT_NAME=aquademie2025
docker compose -f docker-compose.prod.yml exec db \
  psql -U aquademie_user -d aquademie_db -c "
SELECT
  (SELECT COUNT(*) FROM gestion_adherent) AS adherents,
  (SELECT COUNT(*) FROM gestion_seance) AS seances;
"
```

Si les compteurs sont à 0 ou incohérents, la restauration a échoué — recommencer depuis le DROP DATABASE.

### Port 8081 déjà utilisé

```bash
sudo ss -tlnp | grep 8081
```

Adapter `WEB_PUBLISHED_PORT` dans `.env` (ex. `8082`) et mettre à jour Nginx en conséquence.

### Conflit de noms de conteneurs / volumes

Vérifier que `COMPOSE_PROJECT_NAME=aquademie2025` est bien défini avant chaque commande sur l'archive.

```bash
docker volume ls | grep aquademie
# aquademie2025_postgres18_data
# aquademie2025_media_data
# … (séparés de aquademie-technique_* ou du projet courant)
```

### Erreur CSRF / host interdit

Vérifier dans `.env` archive :

```env
DJANGO_ALLOWED_HOSTS=2025.app-suivitech.fr,127.0.0.1,localhost,145.239.78.71
DJANGO_CSRF_TRUSTED_ORIGINS=https://2025.app-suivitech.fr
```

Puis :

```bash
export COMPOSE_PROJECT_NAME=aquademie2025
docker compose -f docker-compose.prod.yml up -d --force-recreate web
```

### Media manquants (404 sur photos/CACI)

Refaire l'étape 6 ou vérifier le contenu du volume :

```bash
export COMPOSE_PROJECT_NAME=aquademie2025
docker compose -f docker-compose.prod.yml exec web find /app/media -type f | head -20
```

### L'archive affiche les données de la nouvelle saison

Vous avez probablement restauré dans le mauvais projet Compose ou sans `COMPOSE_PROJECT_NAME`. Vérifier le volume PostgreSQL monté :

```bash
docker inspect "$(docker compose -f docker-compose.prod.yml ps -q db)" | grep -A3 Mounts
```

---

## Documentation associée

- [BASCULE_SAISON.md](BASCULE_SAISON.md) — bascule et **sauvegarde préalable** (source du backup à restaurer ici)
- [DEPLOIEMENT_DOCKER_UBUNTU_VPS.md](DEPLOIEMENT_DOCKER_UBUNTU_VPS.md) — installation initiale VPS
- [DEPLOIEMENT_DOCKER_SYNOLOGY.md](DEPLOIEMENT_DOCKER_SYNOLOGY.md) — variante Synology
