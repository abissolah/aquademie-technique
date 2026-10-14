from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0033_jetonassistant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modelemailadherents',
            name='nom',
            field=models.CharField(max_length=100),
        ),
        migrations.AddConstraint(
            model_name='modelemailadherents',
            constraint=models.UniqueConstraint(
                fields=('nom', 'auteur'),
                name='unique_modele_mail_adherents_nom_auteur',
            ),
        ),
    ]
