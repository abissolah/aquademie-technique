"""Sérialisation JSON du suivi pédagogique pour l'API assistant.

Les règles de validation reprennent le suivi de formation :
une compétence n'est validée que si chacun de ses exercices a la note 3.
"""

from collections import defaultdict

from django.db.models import Prefetch

from .models import (
    Adherent,
    Competence,
    EvaluationExercice,
    Exercice,
    GroupeCompetence,
    Palanquee,
    Seance,
)

HISTORIQUE_MAX = 8
EVOLUTION_MAX = 4

NOTE_LIBELLES = {
    1: "Non maîtrisé",
    2: "En cours d'acquisition",
    3: "Maîtrisé",
}
RAISONS = dict(EvaluationExercice.RAISON_NON_REALISE_CHOICES)
ECHELLE = {
    "1": NOTE_LIBELLES[1],
    "2": NOTE_LIBELLES[2],
    "3": NOTE_LIBELLES[3],
    "null": "Pas encore évalué ou non réalisé",
}


def note_libelle(note):
    if note is None:
        return None
    return NOTE_LIBELLES.get(note, str(note))


def raison_libelle(code):
    if not code:
        return None
    return RAISONS.get(code, code)


def section_json(section):
    return {
        "id": section.id,
        "code": section.nom,
        "libelle": section.get_nom_display(),
    }


def resume_eleve(eleve, aptitude=None):
    data = {
        "id": eleve.id,
        "nom": eleve.nom,
        "prenom": eleve.prenom,
        "nom_complet": eleve.nom_complet,
        "niveau": eleve.niveau,
        "niveau_libelle": eleve.get_niveau_display(),
        "sections": [section_json(section) for section in eleve.sections.all()],
    }
    if aptitude is not None:
        data["aptitude"] = aptitude or None
    return data


def _groupes_pour_sections(section_ids):
    competences = Competence.objects.order_by("nom").prefetch_related("exercices")
    return (
        GroupeCompetence.objects.filter(section_id__in=section_ids)
        .prefetch_related(Prefetch("competences", queryset=competences))
        .order_by("section_id", "intitule")
    )


def _exercices_du_type(competence, exercice_type):
    return sorted(
        (ex for ex in competence.exercices.all() if ex.type == exercice_type),
        key=lambda ex: ex.nom,
    )


def _indexer_evaluations(eleve_ids, exercice_type):
    """Évaluations les plus récentes en premier, par élève puis par exercice."""
    if not eleve_ids:
        return {}
    evaluations = (
        EvaluationExercice.objects.filter(
            eleve_id__in=eleve_ids,
            exercice__type=exercice_type,
        )
        .select_related("encadrant", "palanquee", "palanquee__seance")
        .order_by("-date_evaluation", "-pk")
    )
    index = defaultdict(lambda: defaultdict(list))
    for evaluation in evaluations:
        index[evaluation.eleve_id][evaluation.exercice_id].append(evaluation)
    return index


def _date_evaluation(evaluation):
    if evaluation.palanquee_id and evaluation.palanquee and evaluation.palanquee.seance_id:
        return evaluation.palanquee.seance.date.isoformat()
    if evaluation.date_evaluation:
        return evaluation.date_evaluation.date().isoformat()
    return None


def _encadrant_nom(evaluation):
    if evaluation.encadrant_id and evaluation.encadrant:
        return evaluation.encadrant.nom_complet
    return "Validé par le DT"


def _historique(evaluations):
    fenetre = list(reversed(evaluations[:HISTORIQUE_MAX]))
    return [
        {
            "date": _date_evaluation(evaluation),
            "note": evaluation.note,
            "note_libelle": note_libelle(evaluation.note),
            "commentaire": evaluation.commentaire or "",
            "raison": raison_libelle(evaluation.raison_non_realise),
            "encadrant": _encadrant_nom(evaluation),
            "palanquee": evaluation.palanquee.nom if evaluation.palanquee_id else "Validation DT",
        }
        for evaluation in fenetre
    ]


def _stats_notes(evaluations):
    notes = [evaluation.note for evaluation in evaluations if evaluation.note]
    derniere = evaluations[0] if evaluations else None
    derniere_note = derniere.note if derniere and derniere.note else None
    return {
        "derniere_note": derniere_note,
        "derniere_note_libelle": note_libelle(derniere_note),
        "note_max": max(notes) if notes else None,
        "nb_evaluations": len(notes),
        "evolution": list(reversed(notes[:EVOLUTION_MAX])),
        "commentaire": (derniere.commentaire or "") if derniere else "",
        "raison": raison_libelle(derniere.raison_non_realise) if derniere else None,
    }


def _construire_progression(groupes, exercice_type, evaluations_par_exercice, avec_historique):
    progression = []
    groupes_valides = 0
    competences_total = 0
    competences_valides = 0
    for groupe in groupes:
        competences_data = []
        groupe_valide = True
        competences = list(groupe.competences.all())
        for competence in competences:
            exercices = _exercices_du_type(competence, exercice_type)
            exercices_data = []
            competence_valide = bool(exercices)
            for exercice in exercices:
                evaluations = evaluations_par_exercice.get(exercice.id, [])
                stats = _stats_notes(evaluations)
                if stats["derniere_note"] != 3:
                    competence_valide = False
                exercice_data = {
                    "id": exercice.id,
                    "nom": exercice.nom,
                    **stats,
                }
                if avec_historique:
                    exercice_data["historique"] = _historique(evaluations)
                exercices_data.append(exercice_data)
            if not exercices:
                competence_valide = False
            competences_total += 1
            if competence_valide:
                competences_valides += 1
            else:
                groupe_valide = False
            competences_data.append({
                "id": competence.id,
                "nom": competence.nom,
                "valide": competence_valide,
                "exercices": exercices_data,
            })
        if groupe_valide:
            groupes_valides += 1
        progression.append({
            "id": groupe.id,
            "intitule": groupe.intitule,
            "valide": groupe_valide,
            "competences": competences_data,
        })
    return progression, {
        "groupes_valides": groupes_valides,
        "groupes_total": len(progression),
        "competences_valides": competences_valides,
        "competences_total": competences_total,
    }


def _profil_compact(groupes, exercice_type, evaluations_par_exercice):
    exercices = []
    groupes_valides = 0
    competences_total = 0
    competences_valides = 0
    for groupe in groupes:
        groupe_valide = True
        competences = list(groupe.competences.all())
        for competence in competences:
            exercices_competence = _exercices_du_type(competence, exercice_type)
            competence_valide = bool(exercices_competence)
            for exercice in exercices_competence:
                stats = _stats_notes(evaluations_par_exercice.get(exercice.id, []))
                if stats["derniere_note"] != 3:
                    competence_valide = False
                exercices.append({
                    "exercice_id": exercice.id,
                    "exercice": exercice.nom,
                    "groupe": groupe.intitule,
                    "competence": competence.nom,
                    **stats,
                })
            if not exercices_competence:
                competence_valide = False
            competences_total += 1
            if competence_valide:
                competences_valides += 1
            else:
                groupe_valide = False
        if groupe_valide:
            groupes_valides += 1
    return {
        "groupes_valides": f"{groupes_valides}/{len(groupes)}",
        "competences_valides": f"{competences_valides}/{competences_total}",
        "exercices": exercices,
    }


def suivi_eleve(eleve, exercice_type):
    sections = list(eleve.sections.all())
    groupes = list(_groupes_pour_sections([section.id for section in sections]))
    index = _indexer_evaluations([eleve.id], exercice_type)
    progression, resume = _construire_progression(
        groupes,
        exercice_type,
        index.get(eleve.id, {}),
        avec_historique=True,
    )
    return {
        "eleve": resume_eleve(eleve),
        "type": exercice_type,
        "echelle": ECHELLE,
        "resume": resume,
        "groupes": progression,
    }


def eleves_actifs_section(section):
    return list(
        Adherent.objects.filter(statut="eleve", actif=True, sections=section)
        .distinct()
        .order_by("nom", "prenom")
        .prefetch_related("sections")
    )


def comparaison_section(section, exercice_type):
    eleves = eleves_actifs_section(section)
    groupes = list(_groupes_pour_sections([section.id]))
    index = _indexer_evaluations([eleve.id for eleve in eleves], exercice_type)
    return {
        "section": section_json(section),
        "type": exercice_type,
        "echelle": ECHELLE,
        "eleves": [
            {
                **resume_eleve(eleve),
                **_profil_compact(groupes, exercice_type, index.get(eleve.id, {})),
            }
            for eleve in eleves
        ],
    }


def profils_eleves(eleves, section, exercice_type, aptitudes=None):
    aptitudes = aptitudes or {}
    groupes = list(_groupes_pour_sections([section.id]))
    index = _indexer_evaluations([eleve.id for eleve in eleves], exercice_type)
    return [
        {
            **resume_eleve(eleve, aptitude=aptitudes.get(eleve.id, "")),
            **_profil_compact(groupes, exercice_type, index.get(eleve.id, {})),
        }
        for eleve in eleves
    ]


def catalogue_section(section, exercice_type):
    groupes = []
    for groupe in _groupes_pour_sections([section.id]):
        competences = []
        for competence in groupe.competences.all():
            exercices = [
                {"id": exercice.id, "nom": exercice.nom, "description": exercice.description}
                for exercice in _exercices_du_type(competence, exercice_type)
            ]
            if exercices:
                competences.append({
                    "id": competence.id,
                    "nom": competence.nom,
                    "exercices": exercices,
                })
        if competences:
            groupes.append({
                "id": groupe.id,
                "intitule": groupe.intitule,
                "competences": competences,
            })
    return {
        "section": section_json(section),
        "type": exercice_type,
        "groupes": groupes,
    }


def _lieu_nom(seance):
    if not seance.lieu_id or not seance.lieu:
        return None
    return seance.lieu.nom


def _encadrant_complet(personne):
    if not personne:
        return None
    return personne.nom_complet


def _eleves_palanquee(palanquee):
    eleves = []
    for lien in palanquee.palanqueeeleve_set.all():
        eleve = lien.eleve
        eleves.append({
            "id": eleve.id,
            "nom_complet": eleve.nom_complet,
            "niveau": eleve.niveau,
            "niveau_libelle": eleve.get_niveau_display(),
            "aptitude": lien.aptitude or None,
        })
    return eleves


def resume_palanquee(palanquee):
    return {
        "id": palanquee.id,
        "nom": palanquee.nom,
        "date": palanquee.seance.date.isoformat(),
        "lieu": _lieu_nom(palanquee.seance),
        "type_seance": palanquee.seance.type,
        "section": section_json(palanquee.section),
        "encadrant": _encadrant_complet(palanquee.encadrant),
        "eleves": _eleves_palanquee(palanquee),
    }


def detail_palanquee(palanquee):
    liens = list(palanquee.palanqueeeleve_set.all())
    eleves = [lien.eleve for lien in liens]
    aptitudes = {lien.eleve_id: lien.aptitude for lien in liens}
    exercice_type = palanquee.type_exercice_attendu()
    data = resume_palanquee(palanquee)
    data.update({
        "type_exercice": exercice_type,
        "echelle": ECHELLE,
        "precision_exercices": palanquee.precision_exercices,
        "duree": palanquee.duree,
        "profondeur_max": palanquee.profondeur_max,
        "exercices_prevus": [
            {"id": exercice.id, "nom": exercice.nom}
            for exercice in palanquee.exercices_prevus.all()
        ],
        "eleves": profils_eleves(eleves, palanquee.section, exercice_type, aptitudes),
    })
    return data


def resume_seance(seance):
    return {
        "id": seance.id,
        "date": seance.date.isoformat(),
        "heure_debut": seance.heure_debut.isoformat() if seance.heure_debut else None,
        "heure_fin": seance.heure_fin.isoformat() if seance.heure_fin else None,
        "type": seance.type,
        "type_libelle": seance.get_type_display(),
        "lieu": _lieu_nom(seance),
        "directeur_plongee": _encadrant_complet(seance.directeur_plongee),
        "type_exercice": (
            Exercice.TYPE_EVALUATION if seance.est_sortie else Exercice.TYPE_CLASSIQUE
        ),
    }


def detail_seance(seance):
    inscrits = []
    for inscription in seance.inscriptions.all():
        personne = inscription.personne
        inscrits.append({
            "id": personne.id,
            "nom_complet": personne.nom_complet,
            "niveau": personne.niveau,
            "niveau_libelle": personne.get_niveau_display(),
            "statut": personne.statut,
            "role_pour_seance": inscription.role_pour_seance,
            "sections": [section_json(section) for section in personne.sections.all()],
        })
    palanquees = []
    for palanquee in seance.palanques.all():
        palanquees.append({
            **resume_palanquee(palanquee),
            "precision_exercices": palanquee.precision_exercices,
            "exercices_prevus": [
                {"id": exercice.id, "nom": exercice.nom}
                for exercice in palanquee.exercices_prevus.all()
            ],
        })
    return {
        **resume_seance(seance),
        "inscrits": inscrits,
        "palanquees": palanquees,
    }


def queryset_palanquees():
    return (
        Palanquee.objects.select_related("seance", "seance__lieu", "section", "encadrant")
        .prefetch_related("palanqueeeleve_set__eleve", "exercices_prevus")
        .order_by("-seance__date", "nom")
    )


def queryset_seances():
    return Seance.objects.select_related("lieu", "directeur_plongee").order_by("date", "pk")
