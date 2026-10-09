"""API en lecture seule consommée par le serveur MCP."""

from functools import wraps

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import Adherent, Exercice, JetonAssistant, Seance, Section
from . import suivi_service

GROUPES_AUTORISES = ("encadrant", "codir", "admin")
LIMITE_RECHERCHE_ELEVES = 50


def utilisateur_autorise(user):
    if not user or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=GROUPES_AUTORISES).exists()


def _json(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={"ensure_ascii": False})


def _erreur(message, status):
    return _json({"error": message}, status=status)


def _jeton_depuis_requete(request):
    header = request.headers.get("Authorization", "")
    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    clair = parts[1].strip()
    if not clair:
        return None
    return (
        JetonAssistant.objects.select_related("utilisateur")
        .filter(empreinte=JetonAssistant.empreinte_de(clair), revoque=False)
        .first()
    )


def exiger_jeton(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        jeton = _jeton_depuis_requete(request)
        if jeton is None or not jeton.utilisateur.is_active:
            return _erreur("Jeton invalide ou révoqué.", 401)
        if not utilisateur_autorise(jeton.utilisateur):
            return _erreur("Ce compte n'est pas autorisé à utiliser l'assistant.", 403)
        JetonAssistant.objects.filter(pk=jeton.pk).update(dernier_usage=timezone.now())
        request.assistant_user = jeton.utilisateur
        return view(request, *args, **kwargs)

    return wrapper


def _type_exercice(request):
    valeur = request.GET.get("type", Exercice.TYPE_CLASSIQUE)
    if valeur not in (Exercice.TYPE_CLASSIQUE, Exercice.TYPE_EVALUATION):
        return None
    return valeur


def _limite(request, defaut, maximum):
    try:
        valeur = int(request.GET.get("limite", defaut))
    except (TypeError, ValueError):
        valeur = defaut
    return max(1, min(valeur, maximum))


def _section_depuis_parametre(valeur):
    valeur = (valeur or "").strip()
    if not valeur:
        return None
    if valeur.isdigit():
        return Section.objects.filter(pk=int(valeur)).first()
    valeur_basse = valeur.lower()
    codes = [
        code
        for code, libelle in Section.SECTIONS_CHOICES
        if valeur_basse in code.lower() or valeur_basse in libelle.lower()
    ]
    if not codes:
        return None
    return Section.objects.filter(nom__in=codes).first()


@require_GET
@exiger_jeton
def sections(request):
    data = [suivi_service.section_json(section) for section in Section.objects.order_by("nom")]
    return _json({"sections": data})


@require_GET
@exiger_jeton
def eleves(request):
    recherche = request.GET.get("q", "").strip()
    queryset = Adherent.objects.filter(statut="eleve", actif=True)
    if recherche:
        queryset = queryset.filter(Q(nom__icontains=recherche) | Q(prenom__icontains=recherche))
    section_param = request.GET.get("section", "").strip()
    if section_param:
        section = _section_depuis_parametre(section_param)
        if section is None:
            return _erreur("Section introuvable.", 404)
        queryset = queryset.filter(sections=section)
    eleves_trouves = (
        queryset.distinct().order_by("nom", "prenom").prefetch_related("sections")[:LIMITE_RECHERCHE_ELEVES]
    )
    return _json({"eleves": [suivi_service.resume_eleve(eleve) for eleve in eleves_trouves]})


@require_GET
@exiger_jeton
def suivi_eleve(request, eleve_id):
    exercice_type = _type_exercice(request)
    if exercice_type is None:
        return _erreur("Le paramètre type doit être classique ou evaluation.", 400)
    eleve = get_object_or_404(
        Adherent.objects.prefetch_related("sections"),
        pk=eleve_id,
        statut="eleve",
    )
    return _json(suivi_service.suivi_eleve(eleve, exercice_type))


@require_GET
@exiger_jeton
def comparaison_section(request, section_id):
    exercice_type = _type_exercice(request)
    if exercice_type is None:
        return _erreur("Le paramètre type doit être classique ou evaluation.", 400)
    section = get_object_or_404(Section, pk=section_id)
    return _json(suivi_service.comparaison_section(section, exercice_type))


@require_GET
@exiger_jeton
def catalogue_exercices(request, section_id):
    exercice_type = _type_exercice(request)
    if exercice_type is None:
        return _erreur("Le paramètre type doit être classique ou evaluation.", 400)
    section = get_object_or_404(Section, pk=section_id)
    return _json(suivi_service.catalogue_section(section, exercice_type))


@require_GET
@exiger_jeton
def palanquees(request):
    encadrant = request.GET.get("encadrant", "").strip()
    if not encadrant:
        return _erreur("Paramètre encadrant requis.", 400)
    limite = _limite(request, defaut=5, maximum=20)
    queryset = suivi_service.queryset_palanquees().filter(
        Q(encadrant__nom__icontains=encadrant) | Q(encadrant__prenom__icontains=encadrant)
    )[:limite]
    return _json({"palanquees": [suivi_service.resume_palanquee(palanquee) for palanquee in queryset]})


@require_GET
@exiger_jeton
def palanquee_detail(request, palanquee_id):
    palanquee = get_object_or_404(suivi_service.queryset_palanquees(), pk=palanquee_id)
    return _json(suivi_service.detail_palanquee(palanquee))


@require_GET
@exiger_jeton
def seances(request):
    limite = _limite(request, defaut=10, maximum=30)
    aujourd_hui = timezone.localdate()
    queryset = suivi_service.queryset_seances().filter(date__gte=aujourd_hui)[:limite]
    return _json({"seances": [suivi_service.resume_seance(seance) for seance in queryset]})


@require_GET
@exiger_jeton
def seance_detail(request, seance_id):
    seance = get_object_or_404(
        Seance.objects.select_related("lieu", "directeur_plongee").prefetch_related(
            "inscriptions__personne__sections",
            "palanques__encadrant",
            "palanques__section",
            "palanques__seance__lieu",
            "palanques__exercices_prevus",
            "palanques__palanqueeeleve_set__eleve",
        ),
        pk=seance_id,
    )
    return _json(suivi_service.detail_seance(seance))
