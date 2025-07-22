from django.contrib import admin
from .models import Adherent, Section, Competence, GroupeCompetence, Seance, Evaluation, LienEvaluation

@admin.register(Adherent)
class AdherentAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'email', 'niveau', 'statut', 'date_fin_validite_caci']
    list_filter = ['niveau', 'statut', 'date_fin_validite_caci']
    search_fields = ['nom', 'prenom', 'email']
    date_hierarchy = 'date_creation'
    readonly_fields = ['date_creation', 'date_modification']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'date_naissance', 'adresse', 'email', 'telephone', 'photo')
        }),
        ('Informations de plongée', {
            'fields': ('date_fin_validite_caci', 'niveau', 'statut')
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

class EvaluationInline(admin.TabularInline):
    model = Evaluation
    extra = 0
    readonly_fields = ['date_evaluation']

@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ['palanquee', 'date', 'section', 'encadrant', 'nombre_eleves']
    list_filter = ['date', 'section', 'encadrant']
    search_fields = ['palanquee', 'encadrant__nom', 'encadrant__prenom']
    date_hierarchy = 'date'
    filter_horizontal = ['eleves', 'competences']
    readonly_fields = ['date_creation', 'date_modification']
    inlines = [EvaluationInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('palanquee', 'date', 'section', 'encadrant')
        }),
        ('Participants', {
            'fields': ('eleves', 'competences')
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
    nombre_eleves.short_description = 'Nombre d\'élèves'

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['seance', 'eleve', 'competence', 'note', 'date_evaluation']
    list_filter = ['seance__date', 'seance__section', 'note']
    search_fields = ['eleve__nom', 'eleve__prenom', 'competence__nom']
    readonly_fields = ['date_evaluation']
    date_hierarchy = 'date_evaluation'

@admin.register(LienEvaluation)
class LienEvaluationAdmin(admin.ModelAdmin):
    list_display = ['seance', 'token', 'date_creation', 'date_expiration', 'est_valide']
    list_filter = ['est_valide', 'date_creation', 'date_expiration']
    search_fields = ['seance__palanquee']
    readonly_fields = ['token', 'date_creation']
    date_hierarchy = 'date_creation'
