"""Serveur MCP HTTP. Chaque outil transmet le jeton de l'appelant à l'API Django."""

import asyncio
import os

import httpx
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.transport_security import TransportSecuritySettings

API_BASE = os.environ.get("ASSISTANT_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def _hote_django() -> str:
    """Nom d'hôte accepté par ALLOWED_HOSTS. En Docker, l'URL interne est http://web:8000."""
    explicite = os.environ.get("ASSISTANT_API_HOST", "").strip()
    if explicite:
        return explicite
    for hote in os.environ.get("MCP_ALLOWED_HOSTS", "").split(","):
        hote = hote.strip()
        if hote:
            return hote
    return ""

INSTRUCTIONS = """
Tu aides les encadrants et les directeurs de plongée à préparer les palanquées
et le programme des séances. Tu proposes, tu ne modifies aucune donnée.

Notes des exercices : 1 = non maîtrisé, 2 = en cours d'acquisition, 3 = maîtrisé.
Une compétence n'est validée que si tous ses exercices sont à 3.
Propose uniquement des exercices présents dans le catalogue du club.

Pour constituer des palanquées de niveau proche : seances_a_venir ou detail_seance,
puis comparer_niveaux sur la section des inscrits.
Pour le programme d'une palanquée : rechercher_palanquees ou detail_seance,
puis detail_palanquee, puis catalogue_exercices.
S'il y a plusieurs palanquées, prends la plus récente sauf si une date est précisée.
type_exercice vaut "classique" pour une séance en piscine et "evaluation" pour une sortie en mer.
""".strip()

mcp = MCPServer("rapports-moniteurs", instructions=INSTRUCTIONS)


def _authorization(ctx: Context) -> str:
    headers = ctx.headers
    if not headers:
        return ""
    return headers.get("authorization") or headers.get("Authorization") or ""


async def _get(ctx: Context, path: str, params: dict | None = None) -> dict:
    authorization = _authorization(ctx)
    if not authorization:
        return {
            "error": "Jeton manquant. Le client MCP doit envoyer l'en-tête Authorization: Bearer …",
        }
    query = {cle: valeur for cle, valeur in (params or {}).items() if valeur not in (None, "")}
    entetes = {"Authorization": authorization}
    hote = _hote_django()
    if hote:
        entetes["Host"] = hote
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(
            f"{API_BASE}{path}",
            params=query,
            headers=entetes,
        )
    try:
        body = response.json()
    except ValueError:
        body = {"error": response.text}
    if response.status_code >= 400:
        message = body.get("error", response.reason_phrase) if isinstance(body, dict) else response.reason_phrase
        return {"error": message, "statut": response.status_code}
    return body


@mcp.tool()
async def lister_sections(ctx: Context) -> dict:
    """Liste les sections du club (id, code, libellé). À appeler avant une comparaison de niveaux."""
    return await _get(ctx, "/api/assistant/sections/")


@mcp.tool()
async def rechercher_eleves(ctx: Context, q: str = "", section: str = "") -> dict:
    """Recherche des élèves actifs par nom ou prénom.

    section : id, code (ex. prepa_niveau1) ou libellé. Vide pour toutes les sections.
    """
    return await _get(ctx, "/api/assistant/eleves/", {"q": q, "section": section})


@mcp.tool()
async def suivi_eleve(ctx: Context, eleve_id: int, type_exercice: str = "classique") -> dict:
    """Suivi détaillé d'un élève : groupes, compétences, dernière note, commentaire et historique.

    type_exercice : "classique" (piscine) ou "evaluation" (sortie en mer).
    Notes : 1 non maîtrisé, 2 en cours d'acquisition, 3 maîtrisé.
    """
    return await _get(ctx, f"/api/assistant/eleves/{eleve_id}/suivi/", {"type": type_exercice})


@mcp.tool()
async def comparer_niveaux(ctx: Context, section_id: int, type_exercice: str = "classique") -> dict:
    """Compare le suivi des élèves actifs d'une section pour former des palanquées de niveau proche.

    Chaque élève a un ratio de compétences validées et, par exercice, la dernière note,
    la note max, le nombre d'évaluations et les 4 dernières notes (evolution).
    Notes : 1 non maîtrisé, 2 en cours d'acquisition, 3 maîtrisé.
    Pour les commentaires détaillés d'un élève, appeler suivi_eleve.
    """
    return await _get(ctx, f"/api/assistant/sections/{section_id}/comparaison/", {"type": type_exercice})


@mcp.tool()
async def rechercher_palanquees(ctx: Context, encadrant: str, limite: int = 5) -> dict:
    """Palanquées récentes d'un encadrant (nom ou prénom, ex. Valérie).

    S'il y en a plusieurs, la plus récente est la première. Utiliser ensuite detail_palanquee.
    """
    return await _get(ctx, "/api/assistant/palanquees/", {"encadrant": encadrant, "limite": limite})


@mcp.tool()
async def detail_palanquee(ctx: Context, palanquee_id: int) -> dict:
    """Élèves d'une palanquée avec leur profil compact (dernières notes et évolution).

    Le type d'exercice (classique ou evaluation) est celui de la séance.
    Enchaîner avec catalogue_exercices de la section pour proposer un programme.
    """
    return await _get(ctx, f"/api/assistant/palanquees/{palanquee_id}/")


@mcp.tool()
async def catalogue_exercices(ctx: Context, section_id: int, type_exercice: str = "classique") -> dict:
    """Catalogue réel des exercices d'une section, groupés par compétence.

    Les propositions de programme doivent rester dans cette liste.
    type_exercice : "classique" ou "evaluation".
    """
    return await _get(ctx, f"/api/assistant/sections/{section_id}/exercices/", {"type": type_exercice})


@mcp.tool()
async def seances_a_venir(ctx: Context, limite: int = 10) -> dict:
    """Séances à venir : date, lieu, type, directeur de plongée.

    type_exercice indique s'il faut ensuite utiliser classique ou evaluation.
    """
    return await _get(ctx, "/api/assistant/seances/", {"limite": limite})


@mcp.tool()
async def detail_seance(ctx: Context, seance_id: int) -> dict:
    """Inscrits et palanquées déjà créées pour une séance, avec les exercices prévus.

    Pour proposer des palanquées, appeler comparer_niveaux sur les sections des inscrits.
    Pour proposer un programme, appeler catalogue_exercices avec le type_exercice de la séance.
    """
    return await _get(ctx, f"/api/assistant/seances/{seance_id}/")


def _securite_transport() -> TransportSecuritySettings:
    hotes = [hote.strip() for hote in os.environ.get("MCP_ALLOWED_HOSTS", "").split(",") if hote.strip()]
    if not hotes:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    origines = [origine.strip() for origine in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",") if origine.strip()]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hotes,
        allowed_origins=origines,
    )


async def servir() -> None:
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8080"))
    await mcp.run_streamable_http_async(
        host=host,
        port=port,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        transport_security=_securite_transport(),
    )


def main() -> None:
    asyncio.run(servir())


if __name__ == "__main__":
    main()
