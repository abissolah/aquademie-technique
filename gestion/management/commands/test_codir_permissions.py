from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gestion.utils import is_codir, is_codir_eleve, is_codir_encadrant, can_access_dashboard

class Command(BaseCommand):
    help = 'Teste les permissions Codir'

    def handle(self, *args, **options):
        self.stdout.write('=== Test des permissions Codir ===\n')
        
        # Test avec un utilisateur Codir élève
        try:
            user_eleve = User.objects.get(username='codir_eleve_test')
            self.stdout.write(f'Test avec {user_eleve.username}:')
            self.stdout.write(f'  - is_codir: {is_codir(user_eleve)}')
            self.stdout.write(f'  - is_codir_eleve: {is_codir_eleve(user_eleve)}')
            self.stdout.write(f'  - is_codir_encadrant: {is_codir_encadrant(user_eleve)}')
            self.stdout.write(f'  - can_access_dashboard: {can_access_dashboard(user_eleve)}')
            self.stdout.write(f'  - Groups: {[g.name for g in user_eleve.groups.all()]}')
            self.stdout.write('')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Utilisateur codir_eleve_test non trouvé')
            )
        
        # Test avec un utilisateur Codir encadrant
        try:
            user_encadrant = User.objects.get(username='codir_encadrant_test')
            self.stdout.write(f'Test avec {user_encadrant.username}:')
            self.stdout.write(f'  - is_codir: {is_codir(user_encadrant)}')
            self.stdout.write(f'  - is_codir_eleve: {is_codir_eleve(user_encadrant)}')
            self.stdout.write(f'  - is_codir_encadrant: {is_codir_encadrant(user_encadrant)}')
            self.stdout.write(f'  - can_access_dashboard: {can_access_dashboard(user_encadrant)}')
            self.stdout.write(f'  - Groups: {[g.name for g in user_encadrant.groups.all()]}')
            self.stdout.write('')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Utilisateur codir_encadrant_test non trouvé')
            )
        
        # Test avec un utilisateur admin normal
        try:
            admin_user = User.objects.filter(groups__name='admin').first()
            if admin_user:
                self.stdout.write(f'Test avec admin ({admin_user.username}):')
                self.stdout.write(f'  - is_codir: {is_codir(admin_user)}')
                self.stdout.write(f'  - is_codir_eleve: {is_codir_eleve(admin_user)}')
                self.stdout.write(f'  - is_codir_encadrant: {is_codir_encadrant(admin_user)}')
                self.stdout.write(f'  - can_access_dashboard: {can_access_dashboard(admin_user)}')
                self.stdout.write(f'  - Groups: {[g.name for g in admin_user.groups.all()]}')
            else:
                self.stdout.write(
                    self.style.WARNING('Aucun utilisateur admin trouvé')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors du test admin: {e}')
            )
