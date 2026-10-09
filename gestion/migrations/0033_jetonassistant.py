import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("gestion", "0032_adherent_niveau4_gp"),
    ]

    operations = [
        migrations.CreateModel(
            name="JetonAssistant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("libelle", models.CharField(blank=True, help_text="Ex. : Cursor de Valérie", max_length=100, verbose_name="Libellé")),
                ("empreinte", models.CharField(editable=False, max_length=64, unique=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("dernier_usage", models.DateTimeField(blank=True, null=True)),
                ("revoque", models.BooleanField(default=False, verbose_name="Révoqué")),
                (
                    "utilisateur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="jetons_assistant",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Utilisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Jeton assistant",
                "verbose_name_plural": "Jetons assistant",
                "ordering": ["-date_creation"],
            },
        ),
    ]
