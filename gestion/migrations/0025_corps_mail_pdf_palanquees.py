# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0024_evaluationexercice_null_palanquee_encadrant'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorpsMailPdfPalanquees',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('corps_html', models.TextField(
                    blank=True,
                    default='',
                    help_text='Syntaxe Django possible : {{ palanquee }}, {{ seance }} '
                    '(ex. palanquee.encadrant.prenom, palanquee.nom, seance.date).',
                    verbose_name='Corps du message (HTML)',
                )),
            ],
            options={
                'verbose_name': 'Corps du mail PDF palanquées (mémorisé)',
                'verbose_name_plural': 'Corps du mail PDF palanquées (mémorisé)',
            },
        ),
    ]
