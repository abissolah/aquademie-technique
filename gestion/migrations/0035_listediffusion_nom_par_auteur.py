from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0034_modelemailadherents_nom_par_auteur'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listediffusion',
            name='nom',
            field=models.CharField(max_length=100, verbose_name='Nom de la liste'),
        ),
        migrations.AddConstraint(
            model_name='listediffusion',
            constraint=models.UniqueConstraint(
                fields=('nom', 'auteur'),
                name='unique_liste_diffusion_nom_auteur',
            ),
        ),
    ]
