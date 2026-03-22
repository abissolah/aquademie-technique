# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0025_corps_mail_pdf_palanquees'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seance',
            name='directeur_plongee',
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={'statut': 'encadrant'},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='seances_dirigees',
                to='gestion.adherent',
                verbose_name='Directeur de plongée',
            ),
        ),
    ]
