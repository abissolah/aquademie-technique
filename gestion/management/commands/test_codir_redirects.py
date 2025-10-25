from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from django.conf import settings
from gestion.utils import is_codir, is_codir_eleve, is_codir_encadrant

class Command(BaseCommand):
    help = 'Teste la redirection des utilisateurs Codir'

    def handle(self, *args, **options):
        self.stdout.write('=== Test des redirections Codir ===\n')
        
        client = Client()
        
        # Test avec un utilisateur Codir élève
        try:
            user_eleve = User.objects.get(username='codir_eleve_test')
            self.stdout.write(f'Test de connexion avec {user_eleve.username}:')
            
            # Utiliser force_login au lieu de login pour éviter les problèmes d'ALLOWED_HOSTS
            client.force_login(user_eleve)
            self.stdout.write('  ✅ Connexion réussie')
            
            # Tester l'accès au dashboard
            response = client.get('/')
            if response.status_code == 200:
                self.stdout.write('  ✅ Accès au dashboard réussi')
            else:
                self.stdout.write(f'  ❌ Erreur accès dashboard: {response.status_code}')
            
            # Tester l'accès à la liste des adhérents
            response = client.get('/adherents/')
            if response.status_code == 200:
                self.stdout.write('  ✅ Accès à la liste des adhérents réussi')
            else:
                self.stdout.write(f'  ❌ Erreur accès adhérents: {response.status_code}')
            
            # Tester l'accès à la liste des élèves
            response = client.get('/eleves/')
            if response.status_code == 200:
                self.stdout.write('  ✅ Accès à la liste des élèves réussi')
            else:
                self.stdout.write(f'  ❌ Erreur accès élèves: {response.status_code}')
            
            client.logout()
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Utilisateur codir_eleve_test non trouvé')
            )
        
        self.stdout.write('')
        
        # Test avec un utilisateur Codir encadrant
        try:
            user_encadrant = User.objects.get(username='codir_encadrant_test')
            self.stdout.write(f'Test de connexion avec {user_encadrant.username}:')
            
            # Utiliser force_login au lieu de login
            client.force_login(user_encadrant)
            self.stdout.write('  ✅ Connexion réussie')
            
            # Tester l'accès au dashboard
            response = client.get('/')
            if response.status_code == 200:
                self.stdout.write('  ✅ Accès au dashboard réussi')
            else:
                self.stdout.write(f'  ❌ Erreur accès dashboard: {response.status_code}')
            
            client.logout()
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Utilisateur codir_encadrant_test non trouvé')
            )
        
        self.stdout.write('\n=== Test terminé ===')
