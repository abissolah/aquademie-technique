# Déploiement production Docker sur Synology

Guide pour exposer l'application **Aquadémie Paris Plongée** sur Internet en **production**, depuis un NAS Synology, avec :

- **IP publique fixe** Orange Business
- **Nom de domaine** OVH
- **HTTPS** (Let's Encrypt via Synology)
- **PostgreSQL** + **Docker**

> Remplacez dans tout ce document :
> - `aquademie.votredomaine.fr` → votre domaine réel
> - `203.0.113.50` → votre IP publique Orange
> - `192.168.1.100` → l'IP locale de votre Synology

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture réseau](#2-architecture-réseau)
3. [Prérequis](#3-prérequis)
4. [Étape 1 — DNS OVH](#4-étape-1--dns-ovh)
5. [Étape 2 — Box Orange Business (NAT)](#5-étape-2--box-orange-business-nat)
6. [Étape 3 — Préparer le Synology](#6-étape-3--préparer-le-synology)
7. [Étape 4 — Déployer l'application Docker](#7-étape-4--déployer-lapplication-docker)
8. [Étape 5 — Fichier `.env` production](#8-étape-5--fichier-env-production)
9. [Étape 6 — HTTPS et Reverse Proxy DSM](#9-étape-6--https-et-reverse-proxy-dsm)
10. [Étape 7 — Sécurité](#10-étape-7--sécurité)
11. [Étape 8 — Vérifications finales](#11-étape-8--vérifications-finales)
12. [Sauvegardes](#12-sauvegardes)
13. [Mises à jour](#13-mises-à-jour)
14. [Dépannage](#14-dépannage)
15. [Annexe — Développement local](#15-annexe--développement-local)

---

## 1. Vue d'ensemble

Le parcours d'une requête utilisateur :

```
Navigateur
    │  https://aquademie.votredomaine.fr
    ▼
DNS OVH  →  IP publique Orange (203.0.113.50)
    ▼
Box Orange Business  →  NAT ports 80/443
    ▼
Synology NAS (192.168.1.100)
    │  Reverse Proxy DSM (HTTPS + certificat Let's Encrypt)
    ▼
Docker nginx (:8080)
    ▼
Docker Django/Gunicorn (:8000)
    ▼
Docker PostgreSQL
```

**Principe clé** : le HTTPS est géré par le **Reverse Proxy intégré à DSM** (certificat Let's Encrypt gratuit). Docker expose l'application en HTTP interne sur le port **8080**, ce qui évite les conflits avec les services DSM qui utilisent déjà le port 80.

---

## 2. Architecture réseau

### Schéma des ports

| Étape | Port | Protocole | Rôle |
|-------|------|-----------|------|
| Internet → Box | 443 | HTTPS | Accès public sécurisé |
| Internet → Box | 80 | HTTP | Redirection vers HTTPS |
| Box → Synology | 443, 80 | TCP | NAT / redirection de port |
| DSM Reverse Proxy | 443 → 8080 | HTTPS → HTTP | Terminaison SSL |
| Docker nginx | 8080 | HTTP | Fichiers statiques + proxy |
| Docker Gunicorn | 8000 | HTTP | Application Django (interne) |
| PostgreSQL | 5432 | TCP | **Non exposé sur Internet** |

### Fichiers Docker du projet

| Fichier | Rôle |
|---------|------|
| `Dockerfile` | Image Python + dépendances |
| `docker-compose.prod.yml` | Stack production (db + web + nginx) |
| `docker/entrypoint.sh` | Migrations, collectstatic, Gunicorn |
| `docker/nginx/nginx.conf` | Reverse proxy interne |
| `.env` | Configuration production (secret, domaine, BDD) |

---

## 3. Prérequis

### Matériel / logiciel

- NAS Synology, **DSM 7.x**, 4 Go RAM minimum
- **Container Manager** installé
- Accès **SSH** au NAS
- Contrat **Orange Business** avec **IP publique fixe**
- Nom de domaine chez **OVH** (zone DNS accessible)

### Informations à rassembler avant de commencer

| Information | Où la trouver |
|-------------|---------------|
| IP publique fixe | Espace client Orange Business ou `https://ifconfig.me` depuis le réseau du bureau |
| IP locale du NAS | DSM → Panneau de configuration → Réseau |
| IP de la box (passerelle) | Souvent `192.168.1.1` |
| Domaine OVH | Espace client OVH → Noms de domaine |

---

## 4. Étape 1 — DNS OVH

### 4.1 Accéder à la zone DNS

1. Connectez-vous à [https://www.ovh.com/manager/](https://www.ovh.com/manager/)
2. **Noms de domaine** → sélectionnez votre domaine
3. Onglet **Zone DNS**

### 4.2 Créer les enregistrements

Ajoutez ou modifiez ces entrées :

| Type | Sous-domaine | Cible | TTL |
|------|-------------|-------|-----|
| **A** | `aquademie` | `203.0.113.50` (votre IP publique Orange) | 300 |
| **A** | `www` | `203.0.113.50` | 300 |

Cela donne :
- `aquademie.votredomaine.fr` → votre NAS
- `www.aquademie.votredomaine.fr` → votre NAS

> Si l'application est à la racine du domaine (`votredomaine.fr` sans sous-domaine), créez un enregistrement **A** sur `@` pointant vers l'IP publique.

### 4.3 Propagation DNS

La propagation prend de **5 minutes à 1 heure**. Vérifiez depuis votre PC :

```bash
nslookup aquademie.votredomaine.fr
# ou
dig aquademie.votredomaine.fr +short
```

Le résultat doit afficher votre IP publique Orange (`203.0.113.50`).

### 4.4 Délégation DNS

Assurez-vous que les serveurs DNS du domaine sont bien ceux d'OVH (par défaut : `dns10.ovh.net`, `ns10.ovh.net`). Si le domaine utilise des DNS externes (Cloudflare, etc.), configurez les enregistrements A dans cet outil à la place.

---

## 5. Étape 2 — Box Orange Business (NAT)

### 5.1 Accéder à l'interface de la Livebox Pro

1. Ouvrez un navigateur : `http://192.168.1.1` (ou l'IP de votre box)
2. Connectez-vous (identifiants sur l'étiquette de la box ou espace client Orange)

> Sur certaines offres Orange Business, la gestion des redirections se fait via l'**espace client Orange Pro** plutôt que l'interface locale.

### 5.2 Redirections de ports (NAT/PAT)

Créez **deux règles** vers l'IP locale du Synology (`192.168.1.100`) :

| Nom | Protocole | Port externe | IP interne | Port interne |
|-----|-----------|-------------|------------|--------------|
| aquademie-http | TCP | 80 | 192.168.1.100 | 80 |
| aquademie-https | TCP | 443 | 192.168.1.100 | 443 |

> Ces ports 80/443 sur le Synology sont utilisés par le **Reverse Proxy DSM** (pas directement par Docker).

### 5.3 IP publique fixe

Avec Orange Business, l'IP publique est normalement **fixe et routable** (pas de CGNAT). Vérifiez :

```bash
# Depuis un PC du réseau local
curl ifconfig.me
```

Comparez avec l'IP indiquée dans votre contrat Orange. Si les deux correspondent et que le DNS OVH pointe dessus, la chaîne réseau est correcte.

### 5.4 Réservation DHCP pour le NAS

Dans la box Orange, associez l'adresse MAC du Synology à l'IP `192.168.1.100` (bail DHCP statique), pour que l'IP locale ne change pas après un redémarrage.

---

## 6. Étape 3 — Préparer le Synology

### 6.1 IP fixe locale du NAS

1. **Panneau de configuration** → **Réseau** → **Interface réseau**
2. Modifier LAN → **Configuration manuelle** :
   - IP : `192.168.1.100`
   - Masque : `255.255.255.0`
   - Passerelle : `192.168.1.1`
   - DNS : `8.8.8.8` ou DNS de la box

### 6.2 Activer SSH

**Panneau de configuration** → **Terminal et SNMP** → cocher **Activer SSH**.

### 6.3 Créer le dossier applicatif

Via File Station ou SSH :

```bash
mkdir -p /volume1/docker/aquademie
```

### 6.4 Récupérer le code

```bash
ssh admin@192.168.1.100
cd /volume1/docker/aquademie
git clone https://github.com/abissolah/aquademie-technique.git .
```

---

## 7. Étape 4 — Déployer l'application Docker

### 7.1 Créer le fichier `.env`

```bash
cd /volume1/docker/aquademie
cp .env.example .env
nano .env
```

Voir la [section 8](#8-étape-5--fichier-env-production) pour le contenu détaillé.

### 7.2 Construire et démarrer

```bash
cd /volume1/docker/aquademie
sudo docker compose -f docker-compose.prod.yml up -d --build
```

Vérifier :

```bash
sudo docker compose -f docker-compose.prod.yml ps
```

Les 3 conteneurs (`db`, `web`, `nginx`) doivent être **Up**.

### 7.3 Test local (avant HTTPS)

Depuis le réseau local :

```
http://192.168.1.100:8080/
```

Si la page de connexion s'affiche, Docker fonctionne. Le port **8080** est utilisé volontairement pour laisser le port 80 libre à DSM.

### 7.4 Créer le compte administrateur

```bash
sudo docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## 8. Étape 5 — Fichier `.env` production

Exemple complet pour un domaine `aquademie.votredomaine.fr` :

```env
# --- Django ---
DJANGO_SECRET_KEY=votre-cle-generee-avec-secrets-token-urlsafe
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=aquademie.votredomaine.fr,www.aquademie.votredomaine.fr,192.168.1.100
DJANGO_CSRF_TRUSTED_ORIGINS=https://aquademie.votredomaine.fr,https://www.aquademie.votredomaine.fr
DJANGO_SITE_URL=https://aquademie.votredomaine.fr
DJANGO_USE_WHITENOISE=True
DJANGO_BEHIND_PROXY=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True

# --- PostgreSQL ---
POSTGRES_DB=aquademie_db
POSTGRES_USER=aquademie_user
POSTGRES_PASSWORD=MotDePasseFortEtUnique123!
POSTGRES_HOST=db
POSTGRES_PORT=5432

# --- Docker : nginx exposé sur 8080 (DSM gère le 443) ---
WEB_PUBLISHED_PORT=8080

# --- Gunicorn ---
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120

# --- Email (SMTP OVH) ---
EMAIL_HOST=ssl0.ovh.net
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=contact@votredomaine.fr
EMAIL_HOST_PASSWORD=votre_mot_de_passe_smtp
DEFAULT_FROM_EMAIL=Aquadémie Paris Plongée <contact@votredomaine.fr>
EMAIL_CC_DEFAULT=admin@votredomaine.fr
EMAIL_CC_COVOIT=admin@votredomaine.fr
```

### Générer la clé secrète Django

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Variables importantes

| Variable | Pourquoi |
|----------|----------|
| `DJANGO_DEBUG=False` | Obligatoire en production |
| `DJANGO_ALLOWED_HOSTS` | Doit contenir le domaine **et** l'IP locale (pour les tests) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | URLs **https://** exactes (avec le domaine) |
| `DJANGO_SITE_URL` | Utilisée dans les emails (liens d'inscription, invitations) |
| `DJANGO_BEHIND_PROXY=True` | Indique à Django qu'il est derrière le Reverse Proxy HTTPS |
| `WEB_PUBLISHED_PORT=8080` | Évite le conflit avec DSM sur le port 80 |

Après modification du `.env` :

```bash
sudo docker compose -f docker-compose.prod.yml up -d
```

---

## 9. Étape 6 — HTTPS et Reverse Proxy DSM

C'est l'étape qui rend le site accessible publiquement en `https://aquademie.votredomaine.fr`.

### 9.1 Obtenir un certificat Let's Encrypt

1. **Panneau de configuration** → **Sécurité** → **Certificat**
2. **Ajouter** → **Ajouter un nouveau certificat**
3. Choisir **Obtenir un certificat auprès de Let's Encrypt**
4. Renseigner :
   - **Nom de domaine** : `aquademie.votredomaine.fr`
   - **Nom de domaine alternatif** : `www.aquademie.votredomaine.fr` (optionnel)
   - **Email** : votre adresse (notifications d'expiration)
5. Valider

> **Prérequis** : le port 80 doit être accessible depuis Internet (NAT configuré) et le DNS doit pointer vers votre IP publique. Let's Encrypt vérifie le domaine via le port 80.

### 9.2 Configurer le Reverse Proxy

1. **Panneau de configuration** → **Connexion** → **Reverse Proxy**
2. **Créer** → onglet **Source** :

| Champ | Valeur |
|-------|--------|
| Description | Aquadémie HTTPS |
| Protocole | HTTPS |
| Nom d'hôte | `aquademie.votredomaine.fr` |
| Port | 443 |
| Certificat | Le certificat Let's Encrypt créé à l'étape 9.1 |

3. Onglet **Destination** :

| Champ | Valeur |
|-------|--------|
| Protocole | HTTP |
| Nom d'hôte | `localhost` |
| Port | `8080` |

4. Onglet **En-têtes personnalisés** (ajouter si absent) :

| En-tête | Valeur |
|---------|--------|
| `X-Forwarded-Proto` | `https` |
| `X-Forwarded-For` | `$remote_addr` |

5. Enregistrer.

### 9.3 Redirection HTTP → HTTPS

Créer une **deuxième règle** Reverse Proxy (ou activer la redirection dans DSM) :

| Source | Destination |
|--------|-------------|
| HTTP, `aquademie.votredomaine.fr`, port 80 | HTTPS, `aquademie.votredomaine.fr`, port 443 |

DSM propose souvent une case **« Rediriger automatiquement vers HTTPS »** lors de la création du certificat — activez-la.

### 9.4 Résultat attendu

| URL | Comportement |
|-----|-------------|
| `http://aquademie.votredomaine.fr` | Redirige vers HTTPS |
| `https://aquademie.votredomaine.fr` | Application accessible |
| `https://aquademie.votredomaine.fr/admin/` | Interface d'administration |

---

## 10. Étape 7 — Sécurité

### 10.1 Pare-feu Synology

**Panneau de configuration** → **Sécurité** → **Pare-feu** :

| Règle | Action |
|-------|--------|
| Autoriser 80/TCP, 443/TCP | Depuis toutes les IP (ou restreindre si usage interne uniquement) |
| **Bloquer 5432/TCP** | PostgreSQL ne doit **jamais** être exposé sur Internet |
| **Bloquer 8080/TCP** depuis l'extérieur | Le port Docker n'a pas besoin d'être accessible directement (DSM proxy en interne) |

### 10.2 Protection DSM

- Activer la **validation en 2 étapes** sur le compte admin
- Changer le port DSM par défaut (5000/5001) si exposé
- Désactiver le compte `admin` par défaut et utiliser un autre nom
- Maintenir DSM à jour

### 10.3 Fichier `.env`

- Ne **jamais** commiter `.env` dans Git
- Sauvegarder `.env` dans un coffre-fort (gestionnaire de mots de passe)
- Utiliser des mots de passe forts pour `DJANGO_SECRET_KEY` et `POSTGRES_PASSWORD`

### 10.4 Sauvegardes chiffrées

Programmer **Hyper Backup** pour chiffrer les sauvegardes du NAS (voir section 12).

---

## 11. Étape 8 — Vérifications finales

### Checklist de mise en production

- [ ] `nslookup aquademie.votredomaine.fr` retourne l'IP publique Orange
- [ ] Ports 80 et 443 redirigés vers le Synology (box Orange)
- [ ] `docker compose ps` : 3 conteneurs Up
- [ ] `http://192.168.1.100:8080/` fonctionne en local
- [ ] `https://aquademie.votredomaine.fr` fonctionne depuis Internet (4G hors Wi-Fi)
- [ ] Connexion admin OK
- [ ] Envoi d'un email de test (invitation séance)
- [ ] Certificat Let's Encrypt valide (cadenas vert)
- [ ] PostgreSQL **non** accessible depuis Internet

### Test depuis l'extérieur du réseau

Sur votre téléphone en **4G** (pas en Wi-Fi) :

```
https://aquademie.votredomaine.fr
```

### Vérifier les logs

```bash
sudo docker compose -f docker-compose.prod.yml logs -f web
sudo docker compose -f docker-compose.prod.yml logs -f nginx
```

---

## 12. Sauvegardes

### 12.1 Sauvegarde PostgreSQL (quotidienne recommandée)

Créer un script `/volume1/docker/aquademie/backup.sh` :

```bash
#!/bin/bash
BACKUP_DIR="/volume1/backup/aquademie"
mkdir -p "$BACKUP_DIR"
cd /volume1/docker/aquademie
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U aquademie_user aquademie_db \
  > "$BACKUP_DIR/aquademie_$(date +%Y%m%d_%H%M).sql"
# Garder les 30 derniers backups
ls -t "$BACKUP_DIR"/aquademie_*.sql | tail -n +31 | xargs -r rm
```

```bash
chmod +x /volume1/docker/aquademie/backup.sh
```

Planifier dans **Planificateur de tâches** DSM (ex. tous les jours à 2h00).

### 12.2 Données à sauvegarder

| Élément | Méthode |
|---------|---------|
| Base PostgreSQL | Script `backup.sh` ci-dessus |
| Fichiers uploadés (CACI, photos) | Volume Docker `media_data` |
| Configuration | Fichier `.env` (hors Git, copie sécurisée) |
| Certificats DSM | Sauvegarde DSM intégrée |

### 12.3 Restauration

```bash
# Arrêter l'application
sudo docker compose -f docker-compose.prod.yml stop web

# Restaurer
cat ./aquademie_backup_last.backup | \
  sudo docker-compose -f docker-compose.prod.yml exec -T db \
  psql -U aquademie_use_25-26 -d aquademie_db_25-26

# Redémarrer
sudo docker compose -f docker-compose.prod.yml start web
```

---

## 13. Mises à jour

```bash
cd /volume1/docker/aquademie

# Sauvegarde avant mise à jour
./backup.sh

# Récupérer le code
git pull

# Reconstruire et redémarrer
sudo docker compose -f docker-compose.prod.yml up -d --build

# Vérifier
sudo docker compose -f docker-compose.prod.yml logs -f web
```

Les migrations Django sont appliquées automatiquement au démarrage.

---

## 14. Dépannage

### Le domaine ne répond pas

| Vérification | Commande / action |
|--------------|-------------------|
| DNS | `nslookup aquademie.votredomaine.fr` |
| IP publique | `curl ifconfig.me` depuis le LAN |
| NAT box Orange | Vérifier redirections 80/443 |
| Conteneurs | `docker compose -f docker-compose.prod.yml ps` |
| Logs | `docker compose -f docker-compose.prod.yml logs web` |

### Erreur « Container is unhealthy » (web ne démarre pas)

Le service `web` attend que PostgreSQL (`db`) soit **healthy**. L'erreur concerne presque toujours **`db`**.

```bash
cd /volume1/docker/aquademie
sudo docker compose -f docker-compose.prod.yml ps -a
sudo docker compose -f docker-compose.prod.yml logs db
```

**Causes fréquentes :**

1. **Fichier `.env` manquant ou incomplet** — vérifier `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
2. **Chemin volume PostgreSQL 18 incorrect** — PG 18+ exige `/var/lib/postgresql` (plus `/data`). Un mauvais chemin provoque un **Restarting** en boucle.
3. **Ancien volume PG 16** sur une image PG 18 — supprimer le volume et relancer

```bash
# Repartir de zéro sur la BDD (⚠️ efface les données)
sudo docker compose -f docker-compose.prod.yml down
sudo docker volume ls | grep postgres
sudo docker volume rm aquademie-technique_postgres_data   # adapter le nom affiché

# Mettre à jour le code (git pull) pour avoir le bon chemin volume PG 18
sudo docker compose -p aquademie-technique -f docker-compose.prod.yml up -d db
sudo docker compose -f docker-compose.prod.yml logs -f db
# Attendre : "database system is ready to accept connections"

sudo docker compose -p aquademie-technique -f docker-compose.prod.yml up -d --build
```

### Erreur « DisallowedHost »

Ajouter le domaine dans `DJANGO_ALLOWED_HOSTS` du `.env`, puis :

```bash
sudo docker compose -f docker-compose.prod.yml up -d
```

### Erreur CSRF (formulaire rejeté)

Vérifier que `DJANGO_CSRF_TRUSTED_ORIGINS` contient l'URL **exacte** avec `https://` :

```env
DJANGO_CSRF_TRUSTED_ORIGINS=https://aquademie.votredomaine.fr
```

### Certificat Let's Encrypt échoue

- Le DNS doit pointer vers l'IP publique **avant** de demander le certificat
- Le port 80 doit être accessible depuis Internet
- Pas de double redirection bloquante sur la box

### Boucle de redirection HTTPS

- Ne pas activer `DJANGO_SECURE_SSL_REDIRECT` (DSM gère déjà le HTTPS)
- Vérifier que `DJANGO_BEHIND_PROXY=True` est bien dans `.env`

### Site accessible en local mais pas depuis Internet

1. Tester le NAT : `https://www.yougetsignal.com/tools/open-ports/` (ports 80 et 443)
2. Vérifier le pare-feu DSM
3. Contacter Orange Business si l'IP publique n'est pas routable (rare sur offre pro)

### Emails non envoyés

Vérifier les variables `EMAIL_*` dans `.env`. Pour OVH, le serveur SMTP est généralement `ssl0.ovh.net` port 465 (SSL).

---

## 15. Annexe — Développement local

Pour tester sur votre PC Windows **avant** le déploiement Synology :

```powershell
cd C:\chemin\vers\rapports_moniteurs
copy .env.example .env
# Modifier .env : DJANGO_DEBUG=True, WEB_PUBLISHED_PORT=8000

docker compose up -d --build
# → http://localhost:8000
```

> Sur Windows, utilisez le port **8000** (le port 80 est souvent bloqué).

---

## Récapitulatif des commandes

| Action | Commande |
|--------|----------|
| Démarrer | `sudo docker compose -f docker-compose.prod.yml up -d --build` |
| Arrêter | `sudo docker compose -f docker-compose.prod.yml down` |
| État | `sudo docker compose -f docker-compose.prod.yml ps` |
| Logs | `sudo docker compose -f docker-compose.prod.yml logs -f web` |
| Admin | `sudo docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser` |
| Backup BDD | `./backup.sh` |
| Mise à jour | `git pull && sudo docker compose -f docker-compose.prod.yml up -d --build` |

---

## Ordre des opérations (résumé)

```
1. DNS OVH        →  domaine pointe vers IP publique Orange
2. NAT Orange     →  ports 80/443 vers Synology
3. Docker         →  docker compose -f docker-compose.prod.yml up -d --build
4. .env           →  domaine, HTTPS, secrets, email
5. Certificat DSM →  Let's Encrypt pour le domaine
6. Reverse Proxy  →  HTTPS:443 → HTTP:8080 (Docker)
7. Test 4G        →  https://aquademie.votredomaine.fr
```

---

## Support

- [Container Manager Synology](https://www.synology.com/fr-fr/dsm/feature/docker)
- [Zone DNS OVH](https://help.ovhcloud.com/csm/fr-dns-edit-dns-zone)
- [Django — Déploiement](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- Déploiement sans Docker : voir [DEPLOIEMENT.md](DEPLOIEMENT.md)
- Bascule de saison : voir [BASCULE_SAISON.md](BASCULE_SAISON.md)
