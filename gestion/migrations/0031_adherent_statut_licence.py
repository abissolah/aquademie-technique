from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0030_adherent_inscription_complement_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='adherent',
            name='statut_licence',
            field=models.CharField(
                choices=[
                    ('a_valider', 'À valider'),
                    ('valide', 'Valide'),
                    ('externe', 'Externe'),
                ],
                default='a_valider',
                max_length=20,
                verbose_name='Statut de licence',
            ),
        ),
    ]
