# Installation en environnement de dev Windows (Git + PostgreSQL)

Ce document explique comment installer et lancer l'application en local sur Windows avec PostgreSQL.

## 1) Prérequis

- Windows 10/11
- [Git for Windows](https://git-scm.com/download/win)
- Python 3.12+ (avec le lanceur `py`)
- PostgreSQL 14+ (serveur + `psql`)

Verification rapide dans PowerShell:

```powershell
git --version
py --version
psql --version
```

## 2) Cloner le projet

```powershell
cd C:\mine\work\perso
git clone <URL_DU_REPO_GIT>
cd rapports_moniteurs
```

## 3) Creer la base PostgreSQL

Se connecter avec un compte admin PostgreSQL (souvent `postgres`):

```powershell
psql -U postgres -h localhost
```

Puis executer:

```sql
CREATE DATABASE rapports_moniteurs_dev ENCODING 'UTF8';
CREATE USER rapports_moniteurs_user WITH PASSWORD 'ChangeMe_123!';
GRANT ALL PRIVILEGES ON DATABASE rapports_moniteurs_dev TO rapports_moniteurs_user;
\q
```

## 4) Configurer Django pour PostgreSQL

Dans `club_plongee/settings.py`, remplacer le bloc `DATABASES` par:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rapports_moniteurs_dev',
        'USER': 'rapports_moniteurs_user',
        'PASSWORD': 'ChangeMe_123!',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

> Option recommandee: utiliser des variables d'environnement pour `USER/PASSWORD`.

## 5) Lancer l'application

### Option A (recommandee): via le script BAT fourni

Depuis la racine du projet:

```powershell
.\start_dev_windows.bat
```

Le script:
- cree le venv s'il n'existe pas
- installe/maj les dependances
- applique les migrations
- lance `python manage.py runserver 0.0.0.0:8000`

### Option B: manuel

```powershell
py -3 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## 6) Creer un compte admin (optionnel)

```powershell
python manage.py createsuperuser
```

Puis ouvrir:
- App: <http://localhost:8000/>
- Admin Django: <http://localhost:8000/admin/>

## 7) Depannage rapide

- `ModuleNotFoundError`: verifier que le venv est bien active.
- Erreur PostgreSQL de connexion: verifier `HOST/PORT/USER/PASSWORD`.
- Port 8000 deja pris:
  - soit arreter le process existant
  - soit lancer sur un autre port (`runserver 0.0.0.0:8001`).

