from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0031_adherent_statut_licence'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adherent',
            name='niveau',
            field=models.CharField(
                choices=[
                    ('debutant', 'Débutant'),
                    ('niveau1', 'Niveau 1'),
                    ('niveau2', 'Niveau 2'),
                    ('niveau3', 'Niveau 3'),
                    ('niveau4', 'Niveau 4 (GP)'),
                    ('initiateur1', 'Initiateur 1'),
                    ('initiateur2', 'Initiateur 2'),
                    ('moniteur_federal1', 'Moniteur fédéral 1'),
                    ('moniteur_federal2', 'Moniteur fédéral 2'),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='ancienadherent',
            name='niveau',
            field=models.CharField(
                choices=[
                    ('debutant', 'Débutant'),
                    ('niveau1', 'Niveau 1'),
                    ('niveau2', 'Niveau 2'),
                    ('niveau3', 'Niveau 3'),
                    ('niveau4', 'Niveau 4 (GP)'),
                    ('initiateur1', 'Initiateur 1'),
                    ('initiateur2', 'Initiateur 2'),
                    ('moniteur_federal1', 'Moniteur fédéral 1'),
                    ('moniteur_federal2', 'Moniteur fédéral 2'),
                ],
                max_length=20,
            ),
        ),
    ]
