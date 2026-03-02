# Generated manually for validation DT (évaluation sans palanquée/encadrant)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0023_add_liste_diffusion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evaluationexercice',
            name='encadrant',
            field=models.ForeignKey(blank=True, limit_choices_to={'statut': 'encadrant'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evaluations_exercices_donnees', to='gestion.adherent'),
        ),
        migrations.AlterField(
            model_name='evaluationexercice',
            name='palanquee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='evaluations_exercices', to='gestion.palanquee'),
        ),
    ]
