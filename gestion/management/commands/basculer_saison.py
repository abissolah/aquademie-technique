from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from gestion.models import (
    Adherent,
    AncienAdherent,
    Evaluation,
    EvaluationExercice,
    InscriptionSeance,
    LienEvaluation,
    LienInscriptionSeance,
    Palanquee,
    Seance,
)


def normaliser_nom_fichier(valeur):
    remplacements = str.maketrans({
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'ô': 'o', 'ö': 'o',
        'î': 'i', 'ï': 'i',
        'ç': 'c',
        'É': 'E', 'È': 'E', 'Ê': 'E',
        'À': 'A', 'Â': 'A',
        'Ù': 'U', 'Û': 'U',
        'Ô': 'O', 'Î': 'I', 'Ç': 'C',
        'Ú': 'e', 'Ó': 'o', 'Ñ': 'n',
    })
    return valeur.translate(remplacements).lower()


def trouver_fichier_local(chemin_relatif, media_root):
    """Retrouve un fichier même si l'encodage du nom a été altéré à la copie."""
    if not chemin_relatif:
        return None
    attendu = media_root / chemin_relatif
    if attendu.exists():
        return attendu
    dossier = attendu.parent
    cible = attendu.name
    if not dossier.is_dir():
        return None
    for chemin in dossier.iterdir():
        if chemin.name.lower() == cible.lower():
            return chemin
    cible_normalisee = normaliser_nom_fichier(cible)
    for chemin in dossier.iterdir():
        if normaliser_nom_fichier(chemin.name) == cible_normalisee:
            return chemin
    return None


class Command(BaseCommand):
    help = (
        'Bascule de saison complète : archive les adhérents, vide Adherent, '
        'purge les séances et données liées.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--saison',
            default='2025-2026',
            help='Saison à archiver (défaut: 2025-2026).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation : affiche les actions sans modifier la base.',
        )
        parser.add_argument(
            '--oui',
            action='store_true',
            help='Confirme l exécution réelle (obligatoire hors dry-run).',
        )
        parser.add_argument(
            '--supprimer-non-adherents',
            action='store_true',
            help='Supprime aussi les non-adhérents (sinon seuls les adhérents sont vidés).',
        )

    def handle(self, *args, **options):
        saison = options['saison']
        dry_run = options['dry_run']
        confirmer = options['oui']
        supprimer_non_adherents = options['supprimer_non_adherents']

        if not dry_run and not confirmer:
            raise CommandError(
                'Pour une exécution réelle, ajoutez --oui '
                '(ou utilisez --dry-run pour simuler).'
            )

        media_root = Path(settings.MEDIA_ROOT)
        manquants = []

        self.stdout.write(self.style.NOTICE('=== Bascule de saison ==='))
        self.stdout.write(f'Saison à archiver : {saison}')
        self.stdout.write(f'Mode : {"DRY-RUN" if dry_run else "RÉEL"}')
        self.stdout.write('')

        with transaction.atomic():
            archives, ignores = self._archiver_adherents(
                saison=saison,
                media_root=media_root,
                manquants=manquants,
                dry_run=dry_run,
            )
            n_adherents = self._vider_adherents(
                supprimer_non_adherents=supprimer_non_adherents,
                dry_run=dry_run,
            )
            stats_seances = self._purger_seances(dry_run=dry_run)

            if dry_run:
                transaction.set_rollback(True)

        total_anciens = AncienAdherent.objects.filter(saison=saison).count()
        restants = Adherent.objects.count()
        seances_restantes = Seance.objects.count()

        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('=== Résumé ==='))
        self.stdout.write(f'Adhérents archivés (cette exécution) : {archives}')
        self.stdout.write(f'Adhérents déjà archivés (ignorés) : {ignores}')
        self.stdout.write(f'Total AncienAdherent saison {saison} : {total_anciens}')
        self.stdout.write(f'Adhérents/supprimés (objets liés) : {n_adherents}')
        self.stdout.write(f'Adherents restants en base : {restants}')
        for cle, valeur in stats_seances.items():
            self.stdout.write(f'{cle} : {valeur}')
        self.stdout.write(f'Séances restantes : {seances_restantes}')
        self.stdout.write(f'Fichiers manquants : {len(manquants)}')
        for item in manquants:
            self.stdout.write(f' - {item}')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run : aucune modification enregistrée.'))
        else:
            self.stdout.write(self.style.SUCCESS('Bascule terminée.'))

    def _archiver_adherents(self, saison, media_root, manquants, dry_run):
        self.stdout.write(self.style.NOTICE('--- 1/3 Archivage des adhérents ---'))
        archives = 0
        ignores = 0
        deja = set(
            AncienAdherent.objects.filter(saison=saison)
            .values_list('nom', 'prenom', 'email')
        )

        def copier_si_possible(source_field, dest_instance, dest_attr, label):
            if not source_field or not source_field.name:
                return
            local = trouver_fichier_local(source_field.name, media_root)
            if not local:
                manquants.append(f'{label}: {source_field.name}')
                self.stdout.write(self.style.WARNING(f'  WARN fichier manquant: {source_field.name}'))
                return
            if dry_run:
                return
            with open(local, 'rb') as fichier:
                contenu = fichier.read()
            getattr(dest_instance, dest_attr).save(local.name, ContentFile(contenu), save=False)

        for adherent in Adherent.objects.filter(type_personne='adherent'):
            cle = (adherent.nom, adherent.prenom, adherent.email)
            if cle in deja:
                ignores += 1
                self.stdout.write(f'Déjà archivé, skip : {adherent.nom} {adherent.prenom}')
                continue

            if dry_run:
                self.stdout.write(f'[dry-run] Archiverait : {adherent.nom} {adherent.prenom}')
                archives += 1
                continue

            ancien = AncienAdherent(
                saison=saison,
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
                autres_brevets=adherent.autres_brevets or '',
                nombre_plongees_milieu_naturel=adherent.nombre_plongees_milieu_naturel or '',
                souhait_perfectionnement_niveau_actuel=adherent.souhait_perfectionnement_niveau_actuel,
                preparation_niveau_superieur=adherent.preparation_niveau_superieur,
                personne_urgence=adherent.personne_urgence or '',
                acceptation_diffusion_image=adherent.acceptation_diffusion_image,
            )
            ancien.save()
            copier_si_possible(adherent.photo, ancien, 'photo', f'{adherent.nom} photo')
            copier_si_possible(adherent.caci_fichier, ancien, 'caci_fichier', f'{adherent.nom} caci')
            ancien.save()
            ancien.sections.set(adherent.sections.all())
            archives += 1
            self.stdout.write(self.style.SUCCESS(f'Archivé : {ancien.nom_complet}'))

        return archives, ignores

    def _vider_adherents(self, supprimer_non_adherents, dry_run):
        self.stdout.write(self.style.NOTICE('--- 2/3 Vidage table Adherent ---'))
        qs = Adherent.objects.all() if supprimer_non_adherents else Adherent.objects.filter(
            type_personne='adherent'
        )
        total = qs.count()
        if dry_run:
            self.stdout.write(f'[dry-run] Supprimerait {total} fiche(s) Adherent')
            return total

        for adherent in qs.filter(user__isnull=False):
            adherent.user = None
            adherent.save(update_fields=['user'])

        count, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f'Adhérents supprimés : {count}'))
        return count

    def _purger_seances(self, dry_run):
        self.stdout.write(self.style.NOTICE('--- 3/3 Purge séances et données liées ---'))
        modeles = [
            ('EvaluationExercice', EvaluationExercice),
            ('Evaluation', Evaluation),
            ('LienEvaluation', LienEvaluation),
            ('InscriptionSeance', InscriptionSeance),
            ('LienInscriptionSeance', LienInscriptionSeance),
            ('Palanquee', Palanquee),
            ('Seance', Seance),
        ]
        stats = {}
        for nom, modele in modeles:
            n = modele.objects.count()
            stats[nom] = n
            if dry_run:
                self.stdout.write(f'[dry-run] Supprimerait {n} {nom}')
            else:
                modele.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'{nom} supprimés : {n}'))
        return stats
