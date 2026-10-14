# Déployer le serveur MCP en production

Le serveur MCP aide les encadrants et les directeurs de plongée à préparer les palanquées et le programme des séances. Il est en lecture seule : l'IA propose, la saisie reste dans l'application.

Cursor ou Claude envoie ses questions à `https://<domaine>/mcp`. Nginx transmet au conteneur MCP, qui rappelle l'API Django avec le jeton de la personne connectée.

## Prérequis

- La stack Docker de production déjà en place (`docker compose -f docker-compose.prod.yml`).
- Le site accessible en HTTPS via le reverse proxy habituel (Synology, Nginx hôte, etc.). Le conteneur MCP n'a pas de port publié : seul Nginx du compose le joint, sur le réseau interne.
- Un compte Django `is_staff` pour créer les jetons dans l'admin.

## Variables d'environnement

À ajouter dans le `.env` à côté de `docker-compose.prod.yml` :

```env
# URL affichée dans l'admin au moment de créer un jeton (avec https).
ASSISTANT_MCP_PUBLIC_URL=https://suivi.exemple.fr/mcp

# Nom d'hôte public vu par Nginx. Plusieurs valeurs séparées par des virgules si besoin.
MCP_ALLOWED_HOSTS=suivi.exemple.fr

# Host envoyé à Django pour les appels internes (http://web:8000). Doit être dans DJANGO_ALLOWED_HOSTS.
ASSISTANT_API_HOST=suivi.exemple.fr

# Laisser vide si les clients n'envoient pas d'en-tête Origin.
MCP_ALLOWED_ORIGINS=
```

`ASSISTANT_API_BASE_URL` est déjà fixé à `http://web:8000` dans le compose : le MCP parle à Django sur le réseau Docker, pas par Internet.

Sans `MCP_ALLOWED_HOSTS`, le contrôle du nom d'hôte est désactivé. Le port 8080 ne doit alors pas être publié sur l'hôte.

## Démarrage

Depuis le répertoire du projet :

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Le conteneur `web` applique les migrations au démarrage, y compris la table des jetons. Le conteneur `mcp` écoute en interne sur le port 8080. Nginx expose `/mcp` sur le même port que le site.

Vérifier que les trois services tournent :

```bash
docker compose -f docker-compose.prod.yml ps
```

## Créer un jeton

1. Ouvrir `/admin/` avec un compte administrateur du site.
2. Aller dans **Jetons assistant**, puis **Ajouter**.
3. Choisir le compte de la personne (encadrant, codir, admin ou superutilisateur) et un libellé, par exemple `Cursor de Valérie`.
4. Enregistrer. Le jeton en clair s'affiche **une seule fois** dans le message vert, avec l'URL et l'en-tête à transmettre :

```text
Authorization: Bearer <le jeton>
```

Un jeton lié à un compte élève est refusé à la création. S'il existait quand même, l'API répondrait 403.

Le clair n'est pas stocké. En base, seule une empreinte SHA-256 est conservée. Pour en donner un nouveau, créer un autre jeton et révoquer l'ancien.

## Brancher Cursor

Dans les réglages MCP de Cursor (`mcp.json`) :

```json
{
  "mcpServers": {
    "aquademie": {
      "url": "https://suivi.exemple.fr/mcp",
      "headers": {
        "Authorization": "Bearer LE_JETON"
      }
    }
  }
}
```

L'URL est sans barre finale.

## Brancher Claude Desktop

Dans `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "aquademie": {
      "url": "https://suivi.exemple.fr/mcp",
      "headers": {
        "Authorization": "Bearer LE_JETON"
      }
    }
  }
}
```

Redémarrer Claude Desktop après l'enregistrement.

## Révoquer un accès

Dans l'admin, cocher le jeton et lancer l'action **Révoquer les jetons sélectionnés**. On peut aussi ouvrir le jeton et cocher **Révoqué**. L'appel suivant reçoit une erreur 401. La date de dernier usage permet de voir si le jeton sert encore.

## Ce que l'assistant peut lire

| Outil | Usage |
| --- | --- |
| `seances_a_venir` | Séances à venir, lieu, directeur de plongée |
| `detail_seance` | Inscrits et palanquées déjà créées |
| `comparer_niveaux` | Élèves d'une section, notes et évolution |
| `rechercher_palanquees` | Palanquées récentes d'un encadrant |
| `detail_palanquee` | Profil des élèves de la palanquée |
| `catalogue_exercices` | Exercices réels de la section |
| `rechercher_eleves` / `suivi_eleve` | Recherche puis suivi détaillé |
| `lister_sections` | Identifiants des sections |

Les notes sont 1 (non maîtrisé), 2 (en cours d'acquisition) et 3 (maîtrisé). Une compétence n'est validée que si tous ses exercices sont à 3. Pour une sortie en mer, le type d'exercice est `evaluation` ; pour une séance en piscine, `classique`.

L'API ne renvoie ni e-mail, ni téléphone, ni adresse, ni CACI, ni contact d'urgence.

## Vérifier après déploiement

Depuis une machine qui joint le site en HTTPS, avec un jeton valide :

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer LE_JETON" \
  -H "Accept: application/json" \
  "https://suivi.exemple.fr/api/assistant/sections/"
```

La réponse attendue est `200`. Un jeton invalide donne `401`.

Le point `/mcp` parle le protocole MCP (pas une page HTML). Le contrôle utile est l'apparition des outils dans Cursor ou Claude, puis une question du type : « Quelles sont les prochaines séances ? ».

## 404 Django sur /mcp

Sur `app-suivitech.fr`, le Nginx du système proxifie tout vers `http://127.0.0.1:8080`. Ce port est le Nginx Docker. Tant qu'il n'a pas rechargé sa configuration, `/mcp` suit la route `/` et Django répond 404. Un 502 voudrait dire que la route existe mais que le conteneur `mcp` est arrêté.

Sur le VPS, dans le répertoire du projet :

```bash
docker compose -f docker-compose.prod.yml up -d --build mcp
docker compose -f docker-compose.prod.yml exec nginx nginx -t
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
curl -sI -H "Host: app-suivitech.fr" http://127.0.0.1:8080/mcp
```

La réponse locale ne doit plus être une page 404 Django. Ensuite seulement, retester `https://app-suivitech.fr/mcp` depuis Cursor.

Dans le `.env` du serveur :

```env
ASSISTANT_MCP_PUBLIC_URL=https://app-suivitech.fr/mcp
MCP_ALLOWED_HOSTS=app-suivitech.fr,www.app-suivitech.fr
ASSISTANT_API_HOST=app-suivitech.fr
```

Puis `docker compose -f docker-compose.prod.yml up -d mcp` pour prendre ces variables.

## Dépannage

- **401 Jeton invalide ou révoqué** : le jeton collé ne correspond plus, ou il a été révoqué. En créer un nouveau.
- **403** : le compte n'est pas dans les groupes encadrant, codir ou admin.
- **404 Django sur `https://<domaine>/mcp`** : la requête arrive sur Django. Le Nginx du VPS envoie déjà tout vers `127.0.0.1:8080` ; c'est le Nginx Docker qui n'a pas rechargé `docker/nginx/nginx.conf`. Voir ci-dessous.
- **Les outils n'apparaissent pas** : URL exacte `https://<domaine>/mcp`, en-tête `Authorization` présent, client redémarré.
- **400 Bad Request, page HTML Django vide** : l'appel interne utilise `Host: web`, refusé par `ALLOWED_HOSTS`. Renseigner `ASSISTANT_API_HOST=app-suivitech.fr` dans le `.env`, puis `docker compose -f docker-compose.prod.yml up -d --build mcp`.
- **400 Invalid Host header** : `MCP_ALLOWED_HOSTS` ne contient pas le nom d'hôte envoyé par le reverse proxy. L'ajouter, puis `docker compose -f docker-compose.prod.yml up -d mcp`.
- **Le MCP ne joint pas Django** : les deux services doivent être sur le même compose. `ASSISTANT_API_BASE_URL` reste `http://web:8000`.

Logs :

```bash
docker compose -f docker-compose.prod.yml logs -f mcp
docker compose -f docker-compose.prod.yml logs -f web
```

## Développement local

Avec Django sur la machine (`http://127.0.0.1:8000`) et le virtualenv du projet :

```bash
pip install -r mcp_server/requirements.txt
```

Windows (PowerShell) :

```powershell
$env:ASSISTANT_API_BASE_URL = "http://127.0.0.1:8000"
$env:MCP_HOST = "127.0.0.1"
python -m mcp_server.server
```

Linux :

```bash
export ASSISTANT_API_BASE_URL=http://127.0.0.1:8000
export MCP_HOST=127.0.0.1
python -m mcp_server.server
```

Le serveur écoute alors `http://127.0.0.1:8080/mcp`. Le jeton se crée de la même façon dans l'admin Django. En Docker de développement, le service `mcp` est sur le réseau interne et appelle `http://web:8000` ; il n'est pas publié sur l'hôte.
