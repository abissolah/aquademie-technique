from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from gestion.models import Adherent, Section, Competence, GroupeCompetence, Seance, Palanquee

class Command(BaseCommand):
    help = 'Crée des données de test pour l\'application Club de Plongée'

    def handle(self, *args, **options):
        self.stdout.write('Création des données de test...')

        # Créer les sections
        sections_data = [
            ('bapteme', 'Baptême de plongée'),
            ('prepa_niveau1', 'Préparation au niveau 1'),
            ('prepa_niveau2', 'Préparation au niveau 2'),
            ('prepa_niveau3', 'Préparation au niveau 3'),
            ('prepa_niveau4', 'Préparation au niveau 4'),
            ('niveau3', 'Niveau 3'),
            ('niveau4', 'Niveau 4'),
            ('encadrant', 'Formation encadrant'),
        ]

        sections = {}
        for nom, description in sections_data:
            section, created = Section.objects.get_or_create(
                nom=nom,
                defaults={'description': description}
            )
            sections[nom] = section
            if created:
                self.stdout.write(f'Section créée : {section.get_nom_display()}')

        # Créer des compétences pour chaque section
        competences_data = {
            'bapteme': [
                'Découverte de l\'équipement',
                'Respiration en surface',
                'Immersion progressive',
                'Découverte de l\'apesanteur',
            ],
            'prepa_niveau1': [
                'Préparation de l\'équipement',
                'Contrôle de la flottabilité',
                'Communication sous l\'eau',
                'Gestion de l\'air',
            ],
            'prepa_niveau2': [
                'Navigation sous-marine',
                'Gestion des paliers',
                'Secourisme de base',
                'Plongée en autonomie',
            ],
            'niveau3': [
                'Encadrement de palanquée',
                'Gestion des incidents',
                'Formation des débutants',
                'Organisation de sorties',
            ],
        }

        competences = {}
        for section_nom, competences_list in competences_data.items():
            section = sections[section_nom]
            for competence_nom in competences_list:
                competence, created = Competence.objects.get_or_create(
                    nom=competence_nom,
                    section=section,
                    defaults={'description': f'Compétence pour {section.get_nom_display()}'}
                )
                competences[competence_nom] = competence
                if created:
                    self.stdout.write(f'Compétence créée : {competence_nom}')

        # Créer des adhérents
        adherents_data = [
            {
                'nom': 'Dupont',
                'prenom': 'Jean',
                'email': 'jean.dupont@email.com',
                'telephone': '0123456789',
                'date_naissance': date(1985, 5, 15),
                'adresse': '123 Rue de la Plage\n75001 Paris',
                'niveau': 'moniteur_federal1',
                'statut': 'encadrant',
                'date_fin_validite_caci': date(2026, 12, 31),
            },
            {
                'nom': 'Martin',
                'prenom': 'Marie',
                'email': 'marie.martin@email.com',
                'telephone': '0987654321',
                'date_naissance': date(1990, 8, 22),
                'adresse': '456 Avenue des Océans\n13001 Marseille',
                'niveau': 'initiateur2',
                'statut': 'encadrant',
                'date_fin_validite_caci': date(2025, 6, 30),
            },
            {
                'nom': 'Bernard',
                'prenom': 'Pierre',
                'email': 'pierre.bernard@email.com',
                'telephone': '0555666777',
                'date_naissance': date(1995, 3, 10),
                'adresse': '789 Boulevard de la Mer\n44000 Nantes',
                'niveau': 'niveau2',
                'statut': 'eleve',
                'date_fin_validite_caci': date(2024, 12, 31),
            },
            {
                'nom': 'Petit',
                'prenom': 'Sophie',
                'email': 'sophie.petit@email.com',
                'telephone': '0444333222',
                'date_naissance': date(1992, 11, 5),
                'adresse': '321 Rue du Port\n69001 Lyon',
                'niveau': 'niveau1',
                'statut': 'eleve',
                'date_fin_validite_caci': date(2025, 3, 15),
            },
            {
                'nom': 'Robert',
                'prenom': 'Lucas',
                'email': 'lucas.robert@email.com',
                'telephone': '0333222111',
                'date_naissance': date(1998, 7, 18),
                'adresse': '654 Chemin des Algues\n06000 Nice',
                'niveau': 'debutant',
                'statut': 'eleve',
                'date_fin_validite_caci': date(2025, 9, 20),
            },
        ]

        adherents = {}
        for adherent_data in adherents_data:
            adherent, created = Adherent.objects.get_or_create(
                email=adherent_data['email'],
                defaults=adherent_data
            )
            adherents[adherent.nom_complet] = adherent
            if created:
                self.stdout.write(f'Adhérent créé : {adherent.nom_complet}')

        # Créer des séances de test
        seances_data = [
            {
                'date': date.today() + timedelta(days=7),
                'lieu': 'Piscine municipale de Paris',
                'palanquees': [
                    {
                        'nom': 'Baptême découverte',
                        'section': sections['bapteme'],
                        'encadrant': adherents['Jean Dupont'],
                        'eleves': ['Lucas Robert'],
                        'competences': ['Découverte de l\'équipement', 'Respiration en surface'],
                        'precision_exercices': 'Séance de découverte pour débutant. Focus sur la familiarisation avec l\'équipement et la respiration.',
                    }
                ]
            },
            {
                'date': date.today() + timedelta(days=14),
                'lieu': 'Centre de plongée de Marseille',
                'palanquees': [
                    {
                        'nom': 'Prépa Niveau 1 - Groupe A',
                        'section': sections['prepa_niveau1'],
                        'encadrant': adherents['Marie Martin'],
                        'eleves': ['Sophie Petit', 'Pierre Bernard'],
                        'competences': ['Préparation de l\'équipement', 'Contrôle de la flottabilité'],
                        'precision_exercices': 'Travail sur la préparation autonome de l\'équipement et les exercices de flottabilité.',
                    }
                ]
            },
            {
                'date': date.today() + timedelta(days=21),
                'lieu': 'Base nautique de Nice',
                'palanquees': [
                    {
                        'nom': 'Niveau 2 - Navigation',
                        'section': sections['prepa_niveau2'],
                        'encadrant': adherents['Jean Dupont'],
                        'eleves': ['Pierre Bernard'],
                        'competences': ['Navigation sous-marine', 'Gestion des paliers'],
                        'precision_exercices': 'Exercices de navigation avec boussole et gestion des paliers de décompression.',
                    }
                ]
            },
        ]

        for seance_data in seances_data:
            # Créer d'abord la séance
            seance = Seance.objects.create(
                date=seance_data['date'],
                lieu=seance_data['lieu'],
            )
            
            # Créer les palanquées associées
            for palanquee_data in seance_data['palanquees']:
                palanquee = Palanquee.objects.create(
                    nom=palanquee_data['nom'],
                    seance=seance,
                    section=palanquee_data['section'],
                    encadrant=palanquee_data['encadrant'],
                    precision_exercices=palanquee_data['precision_exercices'],
                )
                
                # Ajouter les élèves
                for eleve_nom in palanquee_data['eleves']:
                    for adherent in adherents.values():
                        if adherent.prenom in eleve_nom:
                            palanquee.eleves.add(adherent)
                            break
                
                # Ajouter les compétences
                for competence_nom in palanquee_data['competences']:
                    if competence_nom in competences:
                        palanquee.competences.add(competences[competence_nom])
                
                self.stdout.write(f'Palanquée créée : {palanquee.nom} dans la séance du {seance.date}')
            
            self.stdout.write(f'Séance créée : {seance.date} - {seance.lieu}')

        self.stdout.write(
            self.style.SUCCESS('Données de test créées avec succès !')
        )
        self.stdout.write('Vous pouvez maintenant vous connecter à l\'application.') 