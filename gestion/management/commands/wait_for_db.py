import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Attend que la base de données PostgreSQL soit disponible.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Délai maximum d attente en secondes (défaut: 60).',
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        start = time.time()

        self.stdout.write('Attente de la base de données...')
        while time.time() - start < timeout:
            try:
                connection = connections['default']
                connection.cursor()
                self.stdout.write(self.style.SUCCESS('Base de données disponible.'))
                return
            except OperationalError:
                self.stdout.write('Base indisponible, nouvelle tentative dans 1 seconde...')
                time.sleep(1)

        self.stderr.write(self.style.ERROR(f'Timeout après {timeout} secondes.'))
        raise SystemExit(1)
