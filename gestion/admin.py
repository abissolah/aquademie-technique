from django.contrib import admin
from .models import Adherent, Section, Competence, GroupeCompetence, Seance, Palanquee, Evaluation, LienEvaluation, Lieu, PalanqueeEleve
from django.contrib.auth.models import User

@admin.register(Adherent)
class AdherentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'statut', 'type_personne', 'user')
    search_fields = ('nom', 'prenom', 'email')
    list_filter = ('statut', 'type_personne')
    raw_id_fields = ('user',)
    date_hierarchy = 'date_creation'
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'date_naissance', 'adresse', 'email', 'telephone', 'photo')
        }),
        ('Informations de plongée', {
            'fields': ('date_delivrance_caci', 'niveau', 'statut')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_modification'),
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
