from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from .assistant_api import utilisateur_autorise
from .models import Adherent, Section, Competence, GroupeCompetence, Seance, Palanquee, Evaluation, LienEvaluation, Lieu, PalanqueeEleve, CorpsMailPdfPalanquees, AncienAdherent, JetonAssistant, ModeleMailAdherents


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (*BaseUserAdmin.list_display, 'password_defined')
    list_filter = (*BaseUserAdmin.list_filter, 'is_active')

    @admin.display(boolean=True, description='Mot de passe défini')
    def password_defined(self, obj):
        return obj.has_usable_password()


@admin.register(Adherent)
class AdherentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'statut', 'statut_licence', 'type_personne', 'user')
    search_fields = ('nom', 'prenom', 'email')
    list_filter = ('statut', 'statut_licence', 'type_personne')
    raw_id_fields = ('user',)
    date_hierarchy = 'date_creation'
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'date_naissance', 'adresse', 'email', 'telephone', 'photo', 'personne_urgence')
        }),
        ('Informations de plongée', {
            'fields': (
                'date_delivrance_caci', 'niveau', 'statut', 'statut_licence', 'autres_brevets',
                'nombre_plongees_milieu_naturel', 'souhait_perfectionnement_niveau_actuel',
                'preparation_niveau_superieur', 'inscription_hello_asso', 'ancien_adherent',
            )
        }),
        ('Consentements', {
            'fields': ('acceptation_diffusion_image',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AncienAdherent)
class AncienAdherentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'saison', 'email', 'date_archivage')
    search_fields = ('nom', 'prenom', 'email')
    list_filter = ('saison', 'statut', 'niveau')
    filter_horizontal = ('sections',)
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('saison', 'nom', 'prenom', 'date_naissance', 'adresse', 'code_postal', 'ville', 'email', 'telephone', 'photo')
        }),
        ('Informations de plongée', {
            'fields': (
                'date_delivrance_caci', 'caci_fichier', 'niveau', 'statut', 'numero_licence', 'assurance',
                'autres_brevets', 'nombre_plongees_milieu_naturel',
                'souhait_perfectionnement_niveau_actuel', 'preparation_niveau_superieur',
                'personne_urgence', 'acceptation_diffusion_image', 'sections',
            )
        }),
        ('Métadonnées', {
            'fields': ('date_archivage',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['nom', 'description']
    search_fields = ['nom']

@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'section', 'description']
    list_filter = ['section']
    search_fields = ['nom', 'description']
    ordering = ['section', 'nom']

@admin.register(GroupeCompetence)
class GroupeCompetenceAdmin(admin.ModelAdmin):
    list_display = ['intitule', 'section']
    list_filter = ['section']
    search_fields = ['intitule']
    filter_horizontal = ['competences']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('section', 'intitule', 'competences')
        }),
        ('Détails', {
            'fields': ('competences_attendues', 'technique', 'modalites_evaluation')
        }),
    )

# Suppression de la classe PalanqueeInline car le ManyToMany 'eleves' utilise un modèle intermédiaire

@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ['date', 'lieu', 'nombre_palanquees']
    list_filter = ['date']
    search_fields = ['lieu']
    date_hierarchy = 'date'
    readonly_fields = ['date_creation', 'date_modification']
    # inlines = [PalanqueeInline]  # supprimé car ManyToMany via modèle intermédiaire
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('date', 'lieu')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def nombre_palanquees(self, obj):
        return obj.palanquees.count()
    nombre_palanquees.short_description = 'Nombre de palanquées'

class EvaluationInline(admin.TabularInline):
    model = Evaluation
    extra = 0
    readonly_fields = ['date_evaluation']

class PalanqueeEleveInline(admin.TabularInline):
    model = PalanqueeEleve
    extra = 0
    fields = ['eleve', 'aptitude']

@admin.register(Palanquee)
class PalanqueeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'seance', 'section', 'encadrant', 'nombre_eleves']
    list_filter = ['seance__date', 'section', 'encadrant']
    search_fields = ['nom', 'encadrant__nom', 'encadrant__prenom']
    date_hierarchy = 'seance__date'
    filter_horizontal = ['competences']
    readonly_fields = ['date_creation', 'date_modification']
    inlines = [PalanqueeEleveInline, EvaluationInline]
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'seance', 'section', 'encadrant')
        }),
        ('Participants', {
            'fields': ('competences',)
        }),
        ('Contenu', {
            'fields': ('precision_exercices',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    def nombre_eleves(self, obj):
        return obj.eleves.count()
    nombre_eleves.short_description = "Nombre d'élèves"

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['palanquee', 'eleve', 'competence', 'note', 'date_evaluation']
    list_filter = ['palanquee__seance__date', 'palanquee__section', 'note']
    search_fields = ['eleve__nom', 'eleve__prenom', 'competence__nom']
    readonly_fields = ['date_evaluation']
    date_hierarchy = 'date_evaluation'

@admin.register(LienEvaluation)
class LienEvaluationAdmin(admin.ModelAdmin):
    list_display = ['palanquee', 'token', 'date_creation', 'date_expiration', 'est_valide']
    list_filter = ['est_valide', 'date_creation', 'date_expiration']
    search_fields = ['palanquee__nom']
    readonly_fields = ['token', 'date_creation']
    date_hierarchy = 'date_creation'

@admin.register(Lieu)
class LieuAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ville', 'code_postal', 'adresse']
    search_fields = ['nom', 'ville', 'code_postal']
    ordering = ['nom', 'ville']


class JetonAssistantAdminForm(forms.ModelForm):
    class Meta:
        model = JetonAssistant
        fields = "__all__"

    def clean_utilisateur(self):
        utilisateur = self.cleaned_data["utilisateur"]
        if not self.instance.pk and not utilisateur_autorise(utilisateur):
            raise ValidationError(
                "Ce compte n'est pas encadrant, codir, admin ou superutilisateur. "
                "L'API refuserait le jeton."
            )
        return utilisateur


@admin.register(JetonAssistant)
class JetonAssistantAdmin(admin.ModelAdmin):
    form = JetonAssistantAdminForm
    list_display = ("utilisateur", "libelle", "date_creation", "dernier_usage", "revoque")
    list_filter = ("revoque",)
    search_fields = ("utilisateur__username", "utilisateur__first_name", "utilisateur__last_name", "libelle")
    autocomplete_fields = ("utilisateur",)
    readonly_fields = ("date_creation", "dernier_usage")
    actions = ("revoquer_jetons",)

    def get_fields(self, request, obj=None):
        if obj is None:
            return ("utilisateur", "libelle")
        return ("utilisateur", "libelle", "revoque", "date_creation", "dernier_usage")

    def save_model(self, request, obj, form, change):
        clair = None
        if not change:
            clair = obj.definir_nouveau_jeton()
        super().save_model(request, obj, form, change)
        if clair:
            url = settings.ASSISTANT_MCP_PUBLIC_URL
            messages.success(
                request,
                "Jeton à transmettre maintenant, il ne sera plus affiché : "
                f"{clair} — URL MCP : {url} — En-tête : Authorization: Bearer {clair}",
            )

    @admin.action(description="Révoquer les jetons sélectionnés")
    def revoquer_jetons(self, request, queryset):
        nombre = queryset.update(revoque=True)
        self.message_user(request, f"{nombre} jeton(s) révoqué(s).")


@admin.register(ModeleMailAdherents)
class ModeleMailAdherentsAdmin(admin.ModelAdmin):
    list_display = ('nom', 'auteur', 'date_creation')
    list_filter = ('auteur',)
    search_fields = ('nom', 'objet', 'auteur__username', 'auteur__first_name', 'auteur__last_name', 'auteur__email')
    raw_id_fields = ('auteur',)
    readonly_fields = ('date_creation',)


@admin.register(CorpsMailPdfPalanquees)
class CorpsMailPdfPalanqueesAdmin(admin.ModelAdmin):
    list_display = ['__str__']

    def has_add_permission(self, request):
        # Un seul enregistrement suffit (singleton pk=1)
        return not CorpsMailPdfPalanquees.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
