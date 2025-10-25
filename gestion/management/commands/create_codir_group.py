from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Crée le groupe Codir pour les utilisateurs'

    def handle(self, *args, **options):
        # Créer le groupe Codir s'il n'existe pas
        codir_group, created = Group.objects.get_or_create(name='codir')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Groupe "Codir" créé avec succès')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Groupe "Codir" existe déjà')
            )
        
        # Afficher les groupes existants
        groups = Group.objects.all()
        self.stdout.write('\nGroupes existants :')
        for group in groups:
            self.stdout.write(f'  - {group.name}')
