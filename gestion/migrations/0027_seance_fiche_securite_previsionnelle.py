from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0026_alter_seance_directeur_plongee_limit_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='seance',
            name='fiche_securite_previsionnelle',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='fiches_securite_previsionnelles/',
                verbose_name='Fiche de sécu prévisionnelle',
            ),
        ),
    ]
