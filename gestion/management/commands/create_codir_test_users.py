from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from gestion.models import Adherent

class Command(BaseCommand):
    help = 'Crée un utilisateur de test Codir'

    def handle(self, *args, **options):
        # Créer le groupe Codir s'il n'existe pas
        codir_group, created = Group.objects.get_or_create(name='codir')
        eleve_group, created = Group.objects.get_or_create(name='eleve')
        
        # Créer un utilisateur de test Codir élève
        username = 'codir_eleve_test'
        email = 'codir.eleve@test.com'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Utilisateur {username} existe déjà')
            )
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password='test123',
                first_name='Codir',
                last_name='Eleve'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Utilisateur {username} créé avec succès')
            )
        
        # Ajouter aux groupes Codir et élève
        user.groups.add(codir_group)
        user.groups.add(eleve_group)
        
        # Créer un profil adhérent associé
        if not hasattr(user, 'adherent_profile'):
            adherent = Adherent.objects.create(
                nom='ELEVE',
                prenom='Codir',
                date_naissance='1990-01-01',
                adresse='123 Rue Test',
                email=email,
                telephone='0123456789',
                niveau='niveau1',
                statut='eleve',
                user=user
            )
            self.stdout.write(
                self.style.SUCCESS('Profil adhérent créé et associé')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Profil adhérent existe déjà')
            )
        
        # Créer un utilisateur de test Codir encadrant
        username2 = 'codir_encadrant_test'
        email2 = 'codir.encadrant@test.com'
        
        if User.objects.filter(username=username2).exists():
            self.stdout.write(
                self.style.WARNING(f'Utilisateur {username2} existe déjà')
            )
            user2 = User.objects.get(username=username2)
        else:
            user2 = User.objects.create_user(
                username=username2,
                email=email2,
                password='test123',
                first_name='Codir',
                last_name='Encadrant'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Utilisateur {username2} créé avec succès')
            )
        
        # Ajouter aux groupes Codir et encadrant
        encadrant_group, created = Group.objects.get_or_create(name='encadrant')
        user2.groups.add(codir_group)
        user2.groups.add(encadrant_group)
        
        # Créer un profil adhérent associé
        if not hasattr(user2, 'adherent_profile'):
            adherent2 = Adherent.objects.create(
                nom='ENCADRANT',
                prenom='Codir',
                date_naissance='1985-01-01',
                adresse='456 Rue Test',
                email=email2,
                telephone='0987654321',
                niveau='moniteur_federal1',
                statut='encadrant',
                user=user2
            )
            self.stdout.write(
                self.style.SUCCESS('Profil adhérent encadrant créé et associé')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Profil adhérent encadrant existe déjà')
            )
        
        self.stdout.write('\nUtilisateurs de test créés :')
        self.stdout.write(f'  - {username} (Codir + Élève) - Mot de passe: test123')
        self.stdout.write(f'  - {username2} (Codir + Encadrant) - Mot de passe: test123')
