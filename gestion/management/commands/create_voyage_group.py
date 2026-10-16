from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Crée le groupe voyage pour les utilisateurs'

    def handle(self, *args, **options):
        voyage_group, created = Group.objects.get_or_create(name='voyage')

        if created:
            self.stdout.write(self.style.SUCCESS('Groupe "voyage" créé avec succès'))
        else:
            self.stdout.write(self.style.WARNING('Groupe "voyage" existe déjà'))

        self.stdout.write('\nGroupes existants :')
        for group in Group.objects.all():
            marque = ' (nouveau)' if group.pk == voyage_group.pk and created else ''
            self.stdout.write(f'  - {group.name}{marque}')
