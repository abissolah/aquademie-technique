# Bascule de saison 2025-2026 → 2026-2027

Ce document décrit la **procédure manuelle** pour archiver la saison écoulée et repartir sur une base vierge (adhérents + séances), avant d'ouvrir la campagne d'inscription publique **2026-2027**.

> **Important** : effectuez une **sauvegarde complète** de la base de données et du dossier `media/` avant toute opération.

---

## Sommaire

1. [Prérequis](#1-prérequis)
2. [Sauvegarde](#2-sauvegarde)
3. [Étape 1 — Archiver les adhérents dans `anciens_adherents`](#3-étape-1--archiver-les-adhérents)
4. [Étape 2 — Vider la table `Adherent`](#4-étape-2--vider-la-table-adherent)
5. [Étape 3 — Purger séances et données liées](#5-étape-3--purger-séances-et-données-liées)
6. [Étape 4 — Appliquer les migrations](#6-étape-4--appliquer-les-migrations)
7. [Étape 5 — Ouvrir la campagne 2026-2027](#7-étape-5--ouvrir-la-campagne-2026-2027)
8. [Étape 6 — Configurer Hello Asso](#8-étape-6--configurer-hello-asso)
9. [Vérifications finales](#9-vérifications-finales)

---

## 1. Prérequis

- Accès SSH ou shell Django (`python manage.py shell`) en production
- Sauvegarde récente testée (dump PostgreSQL + copie `media/`)
- Code déployé avec la migration `0029_ancienadherent_adherent_saison_fields`
- Campagne Hello Asso **2026-2027** créée (URL disponible)

---

## 2. Sauvegarde

### Base PostgreSQL (Docker)

```bash
cd /volume1/docker/aquademie
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U aquademie_user aquademie_db > backup_avant_bascule_$(date +%Y%m%d).sql
```

### Fichiers media

Copier `/volume1/docker/aquademie/media/` (ou le volume Docker `media_data`) vers un emplacement de sauvegarde.

---

## 3. Étape 1 — Archiver les adhérents

Ouvrir un shell Django :

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

Puis exécuter le script suivant (adapter si besoin) :

```python
from gestion.models import Adherent, AncienAdherent, Section
from gestion.adherent_inscription_services import copier_fichier_champ

SAISON = '2025-2026'

for adherent in Adherent.objects.filter(type_personne='adherent'):
    ancien = AncienAdherent(
        saison=SAISON,
        nom=adherent.nom,
        prenom=adherent.prenom,
        date_naissance=adherent.date_naissance,
        adresse=adherent.adresse,
        code_postal=adherent.code_postal,
        ville=adherent.ville,
        email=adherent.email,
        telephone=adherent.telephone,
        numero_licence=adherent.numero_licence,
        assurance=adherent.assurance or '',
        date_delivrance_caci=adherent.date_delivrance_caci,
        niveau=adherent.niveau,
        statut=adherent.statut,
    )
    ancien.save()
    # Copie physique photo et CACI
    if adherent.photo:
        copier_fichier_champ(adherent.photo, ancien, 'photo')
    if adherent.caci_fichier:
        copier_fichier_champ(adherent.caci_fichier, ancien, 'caci_fichier')
    ancien.save()
    # Sections
    ancien.sections.set(adherent.sections.all())
    print(f'Archivé : {ancien.nom_complet}')

print(f'Total archivés : {AncienAdherent.objects.filter(saison=SAISON).count()}')
```

Vérifier dans l'admin Django (`/admin/gestion/ancienadherent/`) que les fiches et fichiers sont présents.

---

## 4. Étape 2 — Vider la table Adherent

> Les **non-adhérents** (`type_personne='non_adherent'`) peuvent être conservés ou supprimés selon votre choix. Ci-dessous : suppression de **tous** les adhérents du club uniquement.

```python
from gestion.models import Adherent

# Détacher les comptes utilisateurs avant suppression (optionnel)
for a in Adherent.objects.filter(type_personne='adherent', user__isnull=False):
    a.user = None
    a.save(update_fields=['user'])

count, _ = Adherent.objects.filter(type_personne='adherent').delete()
print(f'Adhérents supprimés : {count}')
```

---

## 5. Étape 3 — Purger séances et données liées

```python
from gestion.models import Seance, InscriptionSeance, Palanquee, Evaluation, EvaluationExercice, LienEvaluation, LienInscriptionSeance

# Ordre : supprimer les dépendances puis les séances
EvaluationExercice.objects.all().delete()
Evaluation.objects.all().delete()
LienEvaluation.objects.all().delete()
InscriptionSeance.objects.all().delete()
LienInscriptionSeance.objects.all().delete()
Palanquee.objects.all().delete()
Seance.objects.all().delete()

print('Séances et données associées supprimées.')
```

> Conservez les **sections**, **compétences**, **exercices**, **lieux** et **modèles de mail** : ils servent à la nouvelle saison.

---

## 6. Étape 4 — Appliquer les migrations

Si ce n'est pas déjà fait :

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

---

## 7. Étape 5 — Ouvrir la campagne 2026-2027

### URLs publiques

| URL | Statut |
|-----|--------|
| `/adherents/inscription-2025-2026/` | **Fermée** (message + lien vers 2026-2027) |
| `/adherents/inscription-2026-2027/` | **Active** — étape 1 (ancien adhérent ?) |
| `/adherents/inscription-2026-2027/formulaire/` | Formulaire d'inscription |

### Variables `.env`

```env
HELLO_ASSO_URL=https://www.helloasso.com/associations/aquademie-paris-plongee/adhesions/adhesion-aquademie-2026-2027/1
HELLO_ASSO_WEBHOOK_SECRET=votre_secret_aleatoire
```

Redémarrer l'application après modification du `.env`.

---

## 8. Étape 6 — Configurer Hello Asso

### Webhook

1. Dans Hello Asso, configurer un webhook pointant vers :
   ```
   https://votre-domaine.fr/webhooks/helloasso/?secret=VOTRE_SECRET
   ```
   ou avec l'en-tête HTTP `X-HelloAsso-Secret: VOTRE_SECRET`

2. Le webhook recherche l'adhérent par **email** et passe `inscription_hello_asso` à `True`.

3. En attendant la configuration Hello Asso, l'admin peut cocher manuellement **« Inscription Hello Asso réalisée »** sur la fiche adhérent.

### Test webhook (curl)

```bash
curl -X POST https://votre-domaine.fr/webhooks/helloasso/ \
  -H "Content-Type: application/json" \
  -H "X-HelloAsso-Secret: VOTRE_SECRET" \
  -d '{"email": "test@example.com"}'
```

---

## 9. Vérifications finales

- [ ] `AncienAdherent` contient tous les adhérents 2025-2026 avec photos/CACI
- [ ] Table `Adherent` vide (ou uniquement non-adhérents si conservés)
- [ ] Aucune séance / inscription / palanquée résiduelle
- [ ] `/adherents/inscription-2026-2027/` : recherche nom fonctionne
- [ ] Inscription test (ancien + nouveau) OK
- [ ] CACI visible dans le dashboard « non validé »
- [ ] Redirection Hello Asso après étape 1
- [ ] Ancienne URL 2025-2026 affiche « fermée »

---

## Restauration en cas de problème

```bash
# Restaurer la base
cat backup_avant_bascule_YYYYMMDD.sql | docker compose -f docker-compose.prod.yml exec -T db \
  psql -U aquademie_user -d aquademie_db

# Restaurer media/ depuis la sauvegarde
```

---

## Documentation associée

- [DEPLOIEMENT.md](DEPLOIEMENT.md)
- [DEPLOIEMENT_DOCKER_SYNOLOGY.md](DEPLOIEMENT_DOCKER_SYNOLOGY.md)
