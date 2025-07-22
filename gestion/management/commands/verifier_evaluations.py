from django.core.management.base import BaseCommand
from gestion.models import Evaluation, Seance

class Command(BaseCommand):
    help = 'Vérifie les évaluations en base de données'

    def add_arguments(self, parser):
        parser.add_argument('--seance_id', type=int, help='ID de la séance à vérifier')

    def handle(self, *args, **options):
        seance_id = options.get('seance_id')
        
        if seance_id:
            # Vérifier une séance spécifique
            try:
                seance = Seance.objects.get(pk=seance_id)
                self.stdout.write(f'Séance : {seance.palanquee} (ID: {seance.id})')
                
                evaluations = Evaluation.objects.filter(seance=seance)
                self.stdout.write(f'Nombre d\'évaluations trouvées : {evaluations.count()}')
                
                for eval in evaluations:
                    self.stdout.write(f'  - {eval.eleve.nom_complet} - {eval.competence.nom} : {eval.note}/5')
                    
            except Seance.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Séance avec ID {seance_id} non trouvée'))
        else:
            # Afficher toutes les évaluations
            evaluations = Evaluation.objects.all().select_related('seance', 'eleve', 'competence')
            self.stdout.write(f'Total des évaluations en base : {evaluations.count()}')
            
            for eval in evaluations:
                self.stdout.write(f'  - Séance {eval.seance.id} ({eval.seance.palanquee}) : {eval.eleve.nom_complet} - {eval.competence.nom} : {eval.note}/5') 