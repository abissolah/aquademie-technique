# Generated manually for inscription publique 2026-2027

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0029_ancienadherent_adherent_saison_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='adherent',
            name='acceptation_diffusion_image',
            field=models.BooleanField(
                default=False,
                verbose_name=(
                    "J'accepte la diffusion de mon image sur le site internet du club "
                    "ainsi que sur les impressions destinées à faire connaître les activités du club."
                ),
            ),
        ),
        migrations.AddField(
            model_name='adherent',
            name='autres_brevets',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Ex. : RIFAP, NITROX, etc.',
                max_length=255,
                verbose_name='Autres brevets (sous niveau)',
            ),
        ),
        migrations.AddField(
            model_name='adherent',
            name='nombre_plongees_milieu_naturel',
            field=models.CharField(
                blank=True,
                default='',
                max_length=50,
                verbose_name='Nombre de plongées en milieu naturel',
            ),
        ),
        migrations.AddField(
            model_name='adherent',
            name='personne_urgence',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Nom, prénom, ville, téléphone',
                max_length=255,
                verbose_name="Personne à prévenir en cas d'accident",
            ),
        ),
        migrations.AddField(
            model_name='adherent',
            name='preparation_niveau_superieur',
            field=models.BooleanField(
                default=False,
                verbose_name='Je souhaite me préparer au niveau supérieur',
            ),
        ),
        migrations.AddField(
            model_name='adherent',
            name='souhait_perfectionnement_niveau_actuel',
            field=models.BooleanField(
                default=False,
                verbose_name='Souhait de perfectionnement au niveau actuel',
            ),
        ),
        migrations.AddField(
            model_name='ancienadherent',
            name='acceptation_diffusion_image',
            field=models.BooleanField(default=False, verbose_name="Acceptation diffusion d'image"),
        ),
        migrations.AddField(
            model_name='ancienadherent',
            name='autres_brevets',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Autres brevets (sous niveau)',
            ),
        ),
        migrations.AddField(
            model_name='ancienadherent',
            name='nombre_plongees_milieu_naturel',
            field=models.CharField(
                blank=True,
                default='',
                max_length=50,
                verbose_name='Nombre de plongées en milieu naturel',
            ),
        ),
        migrations.AddField(
            model_name='ancienadherent',
            name='personne_urgence',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name="Personne à prévenir en cas d'accident",
            ),
        ),
        migrations.AddField(
            model_name='ancienadherent',
            name='preparation_niveau_superieur',
            field=models.BooleanField(
                default=False,
                verbose_name='Je souhaite me préparer au niveau supérieur',
            ),
        ),
        migrations.AddField(
            model_name='ancienadherent',
            name='souhait_perfectionnement_niveau_actuel',
            field=models.BooleanField(
                default=False,
                verbose_name='Souhait de perfectionnement au niveau actuel',
            ),
        ),
    ]
