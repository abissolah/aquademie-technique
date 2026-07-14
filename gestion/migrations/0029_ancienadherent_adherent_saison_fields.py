# Generated manually for saison 2026-2027

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0028_seance_type_and_exercice_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='AncienAdherent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saison', models.CharField(default='2025-2026', max_length=20, verbose_name='Saison')),
                ('caci_fichier', models.FileField(blank=True, null=True, upload_to='anciens_adherents/caci/', verbose_name='Fichier CACI')),
                ('nom', models.CharField(max_length=100)),
                ('prenom', models.CharField(max_length=100)),
                ('date_naissance', models.DateField()),
                ('adresse', models.TextField()),
                ('code_postal', models.CharField(blank=True, max_length=10, verbose_name='Code postal')),
                ('ville', models.CharField(blank=True, max_length=100, verbose_name='Ville')),
                ('email', models.EmailField(max_length=254)),
                ('telephone', models.CharField(max_length=20)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='anciens_adherents/photos/')),
                ('numero_licence', models.CharField(blank=True, max_length=50, null=True, verbose_name='Numéro de licence')),
                ('assurance', models.CharField(blank=True, choices=[('', 'Aucune assurance'), ('Piscine', 'Piscine'), ('Loisir 1', 'Loisir 1'), ('Loisir 2', 'Loisir 2'), ('Loisir 3', 'Loisir 3'), ('Loisir Top 1', 'Loisir Top 1'), ('Loisir Top 2', 'Loisir Top 2'), ('Loisir Top 3', 'Loisir Top 3')], default='', max_length=20, verbose_name='Assurance')),
                ('date_delivrance_caci', models.DateField(blank=True, null=True, verbose_name='Date de délivrance du CACI')),
                ('niveau', models.CharField(choices=[('debutant', 'Débutant'), ('niveau1', 'Niveau 1'), ('niveau2', 'Niveau 2'), ('niveau3', 'Niveau 3'), ('initiateur1', 'Initiateur 1'), ('initiateur2', 'Initiateur 2'), ('moniteur_federal1', 'Moniteur fédéral 1'), ('moniteur_federal2', 'Moniteur fédéral 2')], max_length=20)),
                ('statut', models.CharField(choices=[('eleve', 'Élève'), ('encadrant', 'Encadrant')], default='eleve', max_length=10)),
                ('date_archivage', models.DateTimeField(auto_now_add=True)),
                ('sections', models.ManyToManyField(blank=True, related_name='anciens_adherents', to='gestion.section', verbose_name='Sections')),
            ],
            options={
                'verbose_name': 'Ancien adhérent',
                'verbose_name_plural': 'Anciens adhérents',
                'ordering': ['nom', 'prenom'],
            },
        ),
        migrations.AddField(
            model_name='adherent',
            name='inscription_hello_asso',
            field=models.BooleanField(default=False, verbose_name='Inscription Hello Asso réalisée'),
        ),
        migrations.AddField(
            model_name='adherent',
            name='ancien_adherent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reinscriptions', to='gestion.ancienadherent', verbose_name='Ancien adhérent (saison précédente)'),
        ),
    ]
