# Bascule de saison 2025-2026 → 2026-2027

Ce document décrit la **procédure manuelle** pour archiver la saison écoulée et repartir sur une base vierge (adhérents + séances), avant d'ouvrir la campagne d'inscription publique **2026-2027**.

Contexte cible : **VPS Ubuntu** (`app-suivitech.fr`, Docker Compose).

> **Important** : effectuez une **sauvegarde complète** de la base de données et du volume `media` avant toute opération.

---

## Sommaire

1. [Prérequis](#1-prérequis)
2. [Sauvegarde](#2-sauvegarde)
3. [Étape 1 — Bascule complète (une seule commande)](#3-étape-1--bascule-complète-une-seule-commande)
4. [Étape 2 — Appliquer les migrations](#4-étape-2--appliquer-les-migrations)
5. [Étape 3 — Ouvrir la campagne 2026-2027](#5-étape-3--ouvrir-la-campagne-2026-2027)
6. [Étape 4 — Configurer Hello Asso](#6-étape-4--configurer-hello-asso)
7. [Vérifications finales](#7-vérifications-finales)
8. [Restauration en cas de problème](#8-restauration-en-cas-de-problème)

---

## 1. Prérequis

| Élément | Valeur VPS |
|---------|------------|
| Serveur | `145.239.78.71` |
| Domaine | `https://app-suivitech.fr` |
| Répertoire projet | `/opt/aquademie/aquademie-technique` |
| Compose | `docker compose -f docker-compose.prod.yml` |
| Base | `aquademie_db` / `aquademie_user` |
| Conteneur app | `web` |

Autres prérequis :

- Accès SSH au VPS
- Sauvegarde récente testée (dump PostgreSQL + archive `media`)
- Code déployé avec la migration `0029_ancienadherent_adherent_saison_fields`
- Campagne Hello Asso **2026-2027** créée (URL disponible)
- Stack Docker démarrée (`db`, `web`, `nginx` Up)

Toutes les commandes ci-dessous partent du répertoire projet :

```bash
cd /opt/aquademie/aquademie-technique
```

---

## 2. Sauvegarde

### 2.1 Base PostgreSQL

```bash
cd /opt/aquademie/aquademie-technique
mkdir -p /opt/backups

docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U aquademie_user -d aquademie_db -F c \
  > /opt/backups/backup_avant_bascule_$(date +%Y%m%d_%H%M).backup
```

Vérifier :

```bash
ls -lh /opt/backups/backup_avant_bascule_*.backup
```

### 2.2 Fichiers media (volume Docker)

```bash
docker compose -f docker-compose.prod.yml exec web tar czf - -C /app media \
  > /opt/backups/media_avant_bascule_$(date +%Y%m%d_%H%M).tar.gz

ls -lh /opt/backups/media_avant_bascule_*.tar.gz
```

> Ne passez à l'étape suivante **que** si les deux fichiers de sauvegarde sont présents et non vides.

---

## 3. Étape 1 — Bascule complète (une seule commande)

Une seule commande Django enchaîne :
1. archivage des adhérents → `AncienAdherent`
2. vidage de la table `Adherent` (adhérents du club)
3. purge des séances / inscriptions / palanquées / évaluations

> Conservez les **sections**, **compétences**, **exercices**, **lieux** et **modèles de mail**.

### 3.1 Déployer la commande sur le VPS

```bash
cd /opt/aquademie/aquademie-technique

# Depuis votre PC :
# scp gestion/management/commands/basculer_saison.py backupadmin@145.239.78.71:/opt/transferts/

# Sur le VPS :
docker cp /opt/transferts/basculer_saison.py \
  "$(docker compose -f docker-compose.prod.yml ps -q web)":/app/gestion/management/commands/basculer_saison.py
```

Ou rebuild si le dépôt VPS est à jour :

```bash
docker compose -f docker-compose.prod.yml up -d --build web
```

### 3.2 Simulation puis exécution

```bash
cd /opt/aquademie/aquademie-technique

# 1) Simulation (aucune écriture)
docker compose -f docker-compose.prod.yml exec web \
  python manage.py basculer_saison --saison 2025-2026 --dry-run

# 2) Exécution réelle (obligatoire : --oui)
docker compose -f docker-compose.prod.yml exec web \
  python manage.py basculer_saison --saison 2025-2026 --oui
```

Options utiles :
- `--supprimer-non-adherents` : vide aussi les non-adhérents
- reprise possible : les adhérents déjà archivés sont ignorés
- fichiers photo/CACI manquants → `WARN`, sans bloquer

### 3.3 Contrôles

```bash
docker compose -f docker-compose.prod.yml exec db \
  psql -U aquademie_user -d aquademie_db -c "
SELECT
  (SELECT COUNT(*) FROM gestion_ancienadherent WHERE saison='2025-2026') AS anciens,
  (SELECT COUNT(*) FROM gestion_adherent) AS adherents,
  (SELECT COUNT(*) FROM gestion_seance) AS seances;
"
```

Admin : `https://app-suivitech.fr/admin/gestion/ancienadherent/`

---

## 4. Étape 2 — Appliquer les migrations

Si ce n'est pas déjà fait :

```bash
cd /opt/aquademie/aquademie-technique
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations gestion
```

La migration `0029_ancienadherent_adherent_saison_fields` doit être cochée `[X]`.

---

## 5. Étape 3 — Ouvrir la campagne 2026-2027

### URLs publiques

| URL | Statut |
|-----|--------|
| `https://app-suivitech.fr/adherents/inscription-2025-2026/` | **Fermée** (message + lien vers 2026-2027) |
| `https://app-suivitech.fr/adherents/inscription-2026-2027/` | **Active** — étape 1 (ancien adhérent ?) |
| `https://app-suivitech.fr/adherents/inscription-2026-2027/formulaire/` | Formulaire d'inscription |

### Variables `.env`

Éditer `/opt/aquademie/aquademie-technique/.env` :

```env
HELLO_ASSO_URL=https://www.helloasso.com/associations/aquademie-paris-plongee/adhesions/adhesion-aquademie-2026-2027/1
HELLO_ASSO_WEBHOOK_SECRET=votre_secret_aleatoire
DJANGO_SITE_URL=https://app-suivitech.fr
```

Générer un secret si besoin :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Redémarrer le conteneur `web` pour recharger le `.env` :

```bash
cd /opt/aquademie/aquademie-technique
docker compose -f docker-compose.prod.yml up -d --force-recreate web
docker compose -f docker-compose.prod.yml logs --tail=40 web
```

---

## 6. Étape 4 — Configurer Hello Asso

### Webhook

1. Dans Hello Asso, configurer un webhook pointant vers :
   ```
   https://app-suivitech.fr/webhooks/helloasso/?secret=VOTRE_SECRET
   ```
   ou avec l'en-tête HTTP `X-HelloAsso-Secret: VOTRE_SECRET`

2. Le webhook recherche l'adhérent par **email** et passe `inscription_hello_asso` à `True`.

3. En attendant la configuration Hello Asso, l'admin peut cocher manuellement **« Inscription Hello Asso réalisée »** sur la fiche adhérent.

### Test webhook (curl)

```bash
curl -X POST https://app-suivitech.fr/webhooks/helloasso/ \
  -H "Content-Type: application/json" \
  -H "X-HelloAsso-Secret: VOTRE_SECRET" \
  -d '{"email": "test@example.com"}'
```

---

## 7. Vérifications finales

- [ ] Sauvegardes présentes dans `/opt/backups/` (BDD + media)
- [ ] `AncienAdherent` contient tous les adhérents 2025-2026 avec photos/CACI
- [ ] Table `Adherent` vide (ou uniquement non-adhérents si conservés)
- [ ] Aucune séance / inscription / palanquée résiduelle
- [ ] `https://app-suivitech.fr/adherents/inscription-2026-2027/` : recherche nom fonctionne
- [ ] Inscription test (ancien + nouveau) OK
- [ ] CACI visible dans le dashboard « non validé »
- [ ] Redirection Hello Asso après inscription
- [ ] Ancienne URL 2025-2026 affiche « fermée »
- [ ] Webhook Hello Asso testé (ou coche manuelle OK)

---

## 8. Restauration en cas de problème

### Restaurer la base (dump custom `-F c`)

```bash
cd /opt/aquademie/aquademie-technique

docker compose -f docker-compose.prod.yml stop web nginx

docker compose -f docker-compose.prod.yml exec db \
  psql -U aquademie_user -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='aquademie_db' AND pid <> pg_backend_pid();"

docker compose -f docker-compose.prod.yml exec db \
  psql -U aquademie_user -d postgres -c "DROP DATABASE IF EXISTS aquademie_db;"

docker compose -f docker-compose.prod.yml exec db \
  psql -U aquademie_user -d postgres -c \
  "CREATE DATABASE aquademie_db OWNER aquademie_user ENCODING 'UTF8' TEMPLATE template0;"

docker cp /opt/backups/backup_avant_bascule_YYYYMMDD_HHMM.backup \
  "$(docker compose -f docker-compose.prod.yml ps -q db)":/tmp/restore.backup

docker compose -f docker-compose.prod.yml exec db \
  pg_restore -U aquademie_user -d aquademie_db \
  --no-owner --role=aquademie_user /tmp/restore.backup

docker compose -f docker-compose.prod.yml up -d
```

### Restaurer media

```bash
cd /opt/aquademie/aquademie-technique

# Vider puis restaurer
docker compose -f docker-compose.prod.yml exec web sh -c "rm -rf /app/media/*"
docker compose -f docker-compose.prod.yml exec -T web \
  tar xzf - -C /app < /opt/backups/media_avant_bascule_YYYYMMDD_HHMM.tar.gz

# Si l'archive contient un dossier media/ racine :
# docker compose -f docker-compose.prod.yml exec web sh -c \
#   "mv /app/media/media/* /app/media/ && rmdir /app/media/media"

docker compose -f docker-compose.prod.yml exec web chmod -R u+rwX,g+rX,o+rX /app/media
docker compose -f docker-compose.prod.yml exec web ls -la /app/media
```

---

## Documentation associée

- [DEPLOIEMENT_DOCKER_UBUNTU_VPS.md](DEPLOIEMENT_DOCKER_UBUNTU_VPS.md) — installation VPS
- [DEPLOIEMENT_DOCKER_SYNOLOGY.md](DEPLOIEMENT_DOCKER_SYNOLOGY.md) — variante Synology
- [DEPLOIEMENT.md](DEPLOIEMENT.md)
