from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from gestion.utils import is_codir, is_codir_eleve, is_codir_encadrant, can_access_dashboard
from gestion.views import CustomLoginView

class Command(BaseCommand):
    help = 'Teste les fonctions de redirection Codir (version alternative)'

    def handle(self, *args, **options):
        self.stdout.write('=== Test des fonctions Codir (version alternative) ===\n')
        
        # Test avec un utilisateur Codir élève
        try:
            user_eleve = User.objects.get(username='codir_eleve_test')
            self.stdout.write(f'Test avec {user_eleve.username}:')
            
            # Tester les fonctions utilitaires
            self.stdout.write(f'  - is_codir: {is_codir(user_eleve)}')
            self.stdout.write(f'  - is_codir_eleve: {is_codir_eleve(user_eleve)}')
            self.stdout.write(f'  - is_codir_encadrant: {is_codir_encadrant(user_eleve)}')
            self.stdout.write(f'  - can_access_dashboard: {can_access_dashboard(user_eleve)}')
            
            # Tester la vue de connexion personnalisée
            factory = RequestFactory()
            request = factory.get('/login/')
            request.user = user_eleve
            
            login_view = CustomLoginView()
            login_view.request = request
            success_url = login_view.get_success_url()
            
            # Simuler la méthode get_success_url
            if user_eleve.groups.filter(name='codir').exists():
                expected_url = reverse('dashboard')
                if success_url == expected_url:
                    self.stdout.write('  ✅ Redirection vers dashboard correcte')
                else:
                    self.stdout.write(f'  ❌ Redirection incorrecte: {success_url} au lieu de {expected_url}')
            else:
                self.stdout.write('  ❌ Utilisateur pas reconnu comme Codir')
            
            self.stdout.write('')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Utilisateur codir_eleve_test non trouvé')
            )
        
        # Test avec un utilisateur Codir encadrant
        try:
            user_encadrant = User.objects.get(username='codir_encadrant_test')
            self.stdout.write(f'Test avec {user_encadrant.username}:')
            
            # Tester les fonctions utilitaires
            self.stdout.write(f'  - is_codir: {is_codir(user_encadrant)}')
            self.stdout.write(f'  - is_codir_eleve: {is_codir_eleve(user_encadrant)}')
            self.stdout.write(f'  - is_codir_encadrant: {is_codir_encadrant(user_encadrant)}')
            self.stdout.write(f'  - can_access_dashboard: {can_access_dashboard(user_encadrant)}')
            
            # Tester la vue de connexion personnalisée
            factory = RequestFactory()
            request = factory.get('/login/')
            request.user = user_encadrant
            
            login_view = CustomLoginView()
            login_view.request = request
            success_url = login_view.get_success_url()
            
            # Simuler la méthode get_success_url
            if user_encadrant.groups.filter(name='codir').exists():
                expected_url = reverse('dashboard')
                if success_url == expected_url:
                    self.stdout.write('  ✅ Redirection vers dashboard correcte')
                else:
                    self.stdout.write(f'  ❌ Redirection incorrecte: {success_url} au lieu de {expected_url}')
            else:
                self.stdout.write('  ❌ Utilisateur pas reconnu comme Codir')
            
            self.stdout.write('')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Utilisateur codir_encadrant_test non trouvé')
            )
        
        # Test avec un utilisateur élève normal (non Codir)
        try:
            # Chercher un utilisateur élève normal
            eleve_user = User.objects.filter(
                groups__name='eleve'
            ).exclude(
                groups__name='codir'
            ).first()
            
            if eleve_user:
                self.stdout.write(f'Test avec élève normal ({eleve_user.username}):')
                
                # Tester les fonctions utilitaires
                self.stdout.write(f'  - is_codir: {is_codir(eleve_user)}')
                self.stdout.write(f'  - is_codir_eleve: {is_codir_eleve(eleve_user)}')
                self.stdout.write(f'  - is_codir_encadrant: {is_codir_encadrant(eleve_user)}')
                self.stdout.write(f'  - can_access_dashboard: {can_access_dashboard(eleve_user)}')
                
                # Tester la vue de connexion personnalisée
                factory = RequestFactory()
                request = factory.get('/login/')
                request.user = eleve_user
                
                login_view = CustomLoginView()
                login_view.request = request
                success_url = login_view.get_success_url()
                
                # Pour un élève normal, devrait aller vers le suivi de formation
                if hasattr(eleve_user, 'adherent_profile') and eleve_user.adherent_profile.statut == 'eleve':
                    expected_url = reverse('suivi_formation_eleve', kwargs={'eleve_id': eleve_user.adherent_profile.pk})
                    if success_url == expected_url:
                        self.stdout.write('  ✅ Redirection vers suivi de formation correcte')
                    else:
                        self.stdout.write(f'  ❌ Redirection incorrecte: {success_url} au lieu de {expected_url}')
                else:
                    self.stdout.write('  ⚠️ Pas de profil adhérent associé')
                
                self.stdout.write('')
            else:
                self.stdout.write(
                    self.style.WARNING('Aucun utilisateur élève normal trouvé')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors du test élève normal: {e}')
            )
        
        self.stdout.write('=== Test terminé ===')
