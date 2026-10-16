from django.db import migrations


def creer_groupe_voyage(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='voyage')


def supprimer_groupe_voyage(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='voyage').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0035_listediffusion_nom_par_auteur'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(creer_groupe_voyage, supprimer_groupe_voyage),
    ]
