from django.db import migrations, models
class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0027_seance_fiche_securite_previsionnelle'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercice',
            name='type',
            field=models.CharField(
                choices=[('classique', 'Exercice classique'), ('evaluation', "Exercice d'évaluation")],
                default='classique',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='seance',
            name='type',
            field=models.CharField(
                choices=[('seance', 'Séance'), ('sortie', 'Sortie en mer')],
                default='seance',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='seance',
            name='lieu',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.PROTECT,
                related_name='seances',
                to='gestion.lieu',
            ),
        ),
        migrations.AddConstraint(
            model_name='seance',
            constraint=models.CheckConstraint(
                check=models.Q(type='sortie') | models.Q(lieu__isnull=False),
                name='seance_lieu_required_for_classic_seance',
            ),
        ),
    ]
