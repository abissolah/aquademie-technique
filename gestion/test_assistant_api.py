from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone

from gestion.models import (
    Adherent,
    Competence,
    EvaluationExercice,
    Exercice,
    GroupeCompetence,
    InscriptionSeance,
    JetonAssistant,
    Lieu,
    Palanquee,
    PalanqueeEleve,
    Seance,
    Section,
)


def creer_adherent(nom, prenom, statut="eleve", email=None):
    return Adherent.objects.create(
        nom=nom,
        prenom=prenom,
        date_naissance=date(2000, 1, 1),
        adresse="1 rue du club",
        email=email or f"{prenom}.{nom}@example.com".lower(),
        telephone="0600000000",
        niveau="niveau1",
        statut=statut,
    )


def creer_jeton(user, clair, revoque=False):
    return JetonAssistant.objects.create(
        utilisateur=user,
        empreinte=JetonAssistant.empreinte_de(clair),
        libelle="test",
        revoque=revoque,
    )


class AssistantApiTests(TestCase):
    def setUp(self):
        self.encadrant_user = User.objects.create_user("encadrant", password="secret")
        self.encadrant_user.groups.add(Group.objects.get_or_create(name="encadrant")[0])
        self.jeton = "jeton-encadrant-test"
        creer_jeton(self.encadrant_user, self.jeton)

        self.section = Section.objects.create(nom="prepa_niveau1")
        self.exercice = Exercice.objects.create(nom="Vidage de masque", description="Retirer et remettre le masque")
        self.competence = Competence.objects.create(nom="Immersion", section=self.section)
        self.competence.exercices.add(self.exercice)
        self.groupe = GroupeCompetence.objects.create(
            section=self.section,
            intitule="Techniques",
            competences_attendues="Maîtriser l'immersion",
            technique="Palmage",
            modalites_evaluation="En piscine",
        )
        self.groupe.competences.add(self.competence)

        self.alice = creer_adherent("DURAND", "Alice")
        self.alice.sections.add(self.section)
        self.bruno = creer_adherent("MARTIN", "Bruno")
        self.bruno.sections.add(self.section)
        self.moniteur = creer_adherent("BERNARD", "Valerie", statut="encadrant", email="valerie@example.com")

        EvaluationExercice.objects.create(eleve=self.alice, exercice=self.exercice, note=1, commentaire="À revoir")
        EvaluationExercice.objects.create(eleve=self.alice, exercice=self.exercice, note=3, commentaire="Acquis")
        EvaluationExercice.objects.create(eleve=self.bruno, exercice=self.exercice, note=1, commentaire="Début")

        self.lieu = Lieu.objects.create(nom="Piscine", adresse="2 rue", code_postal="75011", ville="Paris")
        self.seance = Seance.objects.create(
            date=timezone.localdate() + timedelta(days=3),
            lieu=self.lieu,
            directeur_plongee=self.moniteur,
        )
        self.palanquee = Palanquee.objects.create(
            nom="Palanquée 1",
            seance=self.seance,
            section=self.section,
            encadrant=self.moniteur,
            precision_exercices="Vidage de masque",
        )
        self.palanquee.exercices_prevus.add(self.exercice)
        PalanqueeEleve.objects.create(palanquee=self.palanquee, eleve=self.alice, aptitude="PE20")
        InscriptionSeance.objects.create(seance=self.seance, personne=self.alice, role_pour_seance="eleve")

    def _get(self, url, token=None):
        headers = {}
        if token is not None:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return self.client.get(url, **headers)

    def test_jeton_inconnu(self):
        response = self._get("/api/assistant/sections/", token="inconnu")
        self.assertEqual(response.status_code, 401)

    def test_sans_jeton(self):
        response = self.client.get("/api/assistant/sections/")
        self.assertEqual(response.status_code, 401)

    def test_jeton_revoque(self):
        creer_jeton(self.encadrant_user, "jeton-revoque", revoque=True)
        response = self._get("/api/assistant/sections/", token="jeton-revoque")
        self.assertEqual(response.status_code, 401)

    def test_compte_eleve_refuse(self):
        eleve_user = User.objects.create_user("alice", password="secret")
        eleve_user.groups.add(Group.objects.get_or_create(name="eleve")[0])
        self.alice.user = eleve_user
        self.alice.save()
        creer_jeton(eleve_user, "jeton-eleve")
        response = self._get("/api/assistant/sections/", token="jeton-eleve")
        self.assertEqual(response.status_code, 403)

    def test_affichage_jeton_avec_libelle(self):
        jeton = JetonAssistant.objects.get(utilisateur=self.encadrant_user)
        self.assertIn("test", str(jeton))

    def test_jeton_valide_met_a_jour_le_dernier_usage(self):
        response = self._get("/api/assistant/sections/", token=self.jeton)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sections"][0]["code"], "prepa_niveau1")
        jeton = JetonAssistant.objects.get(utilisateur=self.encadrant_user, revoque=False, libelle="test")
        self.assertIsNotNone(jeton.dernier_usage)

    def test_recherche_eleve_sans_donnees_personnelles(self):
        response = self._get("/api/assistant/eleves/?q=alice", token=self.jeton)
        self.assertEqual(response.status_code, 200)
        eleve = response.json()["eleves"][0]
        self.assertEqual(eleve["prenom"], "Alice")
        self.assertNotIn("email", eleve)
        self.assertNotIn("telephone", eleve)
        self.assertNotIn("adresse", eleve)

    def test_suivi_eleve(self):
        response = self._get(f"/api/assistant/eleves/{self.alice.id}/suivi/", token=self.jeton)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["resume"]["competences_valides"], 1)
        self.assertEqual(data["resume"]["competences_total"], 1)
        exercice = data["groupes"][0]["competences"][0]["exercices"][0]
        self.assertEqual(exercice["derniere_note"], 3)
        self.assertEqual(exercice["evolution"], [1, 3])
        self.assertEqual(exercice["historique"][-1]["commentaire"], "Acquis")
        self.assertNotIn("email", data["eleve"])

    def test_comparaison_section(self):
        response = self._get(
            f"/api/assistant/sections/{self.section.id}/comparaison/",
            token=self.jeton,
        )
        self.assertEqual(response.status_code, 200)
        eleves = {eleve["prenom"]: eleve for eleve in response.json()["eleves"]}
        self.assertEqual(eleves["Alice"]["competences_valides"], "1/1")
        self.assertEqual(eleves["Bruno"]["competences_valides"], "0/1")
        self.assertEqual(eleves["Alice"]["exercices"][0]["derniere_note"], 3)
        self.assertEqual(eleves["Bruno"]["exercices"][0]["derniere_note"], 1)
        self.assertEqual(eleves["Alice"]["exercices"][0]["evolution"], [1, 3])

    def test_detail_seance(self):
        response = self._get(f"/api/assistant/seances/{self.seance.id}/", token=self.jeton)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["directeur_plongee"], "BERNARD Valerie")
        self.assertEqual(data["type_exercice"], "classique")
        self.assertEqual(data["inscrits"][0]["nom_complet"], "DURAND Alice")
        self.assertEqual(data["inscrits"][0]["role_pour_seance"], "eleve")
        self.assertNotIn("email", data["inscrits"][0])
        self.assertEqual(data["palanquees"][0]["nom"], "Palanquée 1")
        self.assertEqual(data["palanquees"][0]["exercices_prevus"][0]["nom"], "Vidage de masque")
        self.assertEqual(data["palanquees"][0]["eleves"][0]["aptitude"], "PE20")

    def test_palanquee_par_encadrant(self):
        response = self._get("/api/assistant/palanquees/?encadrant=Valerie", token=self.jeton)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["palanquees"][0]["id"], self.palanquee.id)

    def test_detail_palanquee(self):
        response = self._get(f"/api/assistant/palanquees/{self.palanquee.id}/", token=self.jeton)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["type_exercice"], "classique")
        self.assertEqual(data["eleves"][0]["aptitude"], "PE20")
        self.assertEqual(data["eleves"][0]["exercices"][0]["derniere_note"], 3)
