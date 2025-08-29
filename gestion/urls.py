from django.urls import path
from . import views
from .palanquee_views import (
    PalanqueeListView, PalanqueeDetailView, PalanqueeCreateView,
    PalanqueeUpdateView, PalanqueeDeleteView,
    palanquee_evaluation, palanquee_evaluation_view,
    generer_lien_evaluation, evaluation_publique,
    generer_fiche_palanquee_pdf, envoyer_lien_par_email
)

urlpatterns = [
    # URLs d'authentification
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # URL d'accueil (dashboard)
    path('', views.dashboard, name='dashboard'),
    
    # Adhérents
    path('adherents/', views.AdherentListView.as_view(), name='adherent_list'),
    path('adherents/<int:pk>/', views.AdherentDetailView.as_view(), name='adherent_detail'),
    path('adherents/nouveau/', views.AdherentCreateView.as_view(), name='adherent_create'),
    path('adherents/<int:pk>/modifier/', views.AdherentUpdateView.as_view(), name='adherent_update'),
    path('adherents/<int:pk>/supprimer/', views.AdherentDeleteView.as_view(), name='adherent_delete'),
    path('adherents/import-excel/', views.import_adherents_excel, name='import_adherents_excel'),
    path('adherents/telecharger-modele/', views.download_excel_template, name='download_excel_template'),
    
    # Élèves
    path('eleves/', views.EleveListView.as_view(), name='eleve_list'),
    
    # Encadrants
    path('encadrants/', views.EncadrantListView.as_view(), name='encadrant_list'),
    
    # Sections
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/<int:pk>/', views.SectionDetailView.as_view(), name='section_detail'),
    path('sections/nouvelle/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<int:pk>/modifier/', views.SectionUpdateView.as_view(), name='section_update'),
    path('sections/<int:pk>/supprimer/', views.SectionDeleteView.as_view(), name='section_delete'),
    
    # Compétences
    path('competences/', views.CompetenceListView.as_view(), name='competence_list'),
    path('competences/nouvelle/', views.CompetenceCreateView.as_view(), name='competence_create'),
    path('competences/<int:pk>/modifier/', views.CompetenceUpdateView.as_view(), name='competence_update'),
    path('competences/<int:pk>/supprimer/', views.CompetenceDeleteView.as_view(), name='competence_delete'),
    
    # Groupes de compétences
    path('groupes-competences/', views.GroupeCompetenceListView.as_view(), name='groupe_competence_list'),
    path('groupes-competences/nouveau/', views.GroupeCompetenceCreateView.as_view(), name='groupe_competence_create'),
    path('groupes-competences/<int:pk>/modifier/', views.GroupeCompetenceUpdateView.as_view(), name='groupe_competence_update'),
    path('groupes-competences/<int:pk>/supprimer/', views.GroupeCompetenceDeleteView.as_view(), name='groupe_competence_delete'),
    
    # Séances
    path('seances/', views.SeanceListView.as_view(), name='seance_list'),
    path('seances/<int:pk>/', views.SeanceDetailView.as_view(), name='seance_detail'),
    path('seances/nouvelle/', views.SeanceCreateView.as_view(), name='seance_create'),
    path('seances/<int:pk>/modifier/', views.SeanceUpdateView.as_view(), name='seance_update'),
    path('seances/<int:pk>/supprimer/', views.SeanceDeleteView.as_view(), name='seance_delete'),
    
    # Palanquées
    path('palanquees/', PalanqueeListView.as_view(), name='palanquee_list'),
    path('palanquees/<int:pk>/', PalanqueeDetailView.as_view(), name='palanquee_detail'),
    path('palanquees/nouvelle/', PalanqueeCreateView.as_view(), name='palanquee_create'),
    path('palanquees/<int:pk>/modifier/', PalanqueeUpdateView.as_view(), name='palanquee_update'),
    path('palanquees/<int:pk>/supprimer/', PalanqueeDeleteView.as_view(), name='palanquee_delete'),
    
    # Évaluations des palanquées
    path('palanquees/<int:pk>/evaluation/', palanquee_evaluation, name='palanquee_evaluation'),
    path('palanquees/<int:pk>/evaluation/voir/', palanquee_evaluation_view, name='palanquee_evaluation_view'),
    
    # Liens d'évaluation
    path('palanquees/<int:pk>/generer-lien/', generer_lien_evaluation, name='generer_lien_evaluation'),
    path('palanquees/<int:pk>/envoyer-email/', envoyer_lien_par_email, name='envoyer_lien_par_email'),
    path('evaluation/<str:token>/', evaluation_publique, name='evaluation_publique'),
    
    # Génération de PDF
    path('palanquees/<int:pk>/pdf/', generer_fiche_palanquee_pdf, name='generer_fiche_palanquee_pdf'),
    
    # Évaluations
    path('evaluations/<int:pk>/', views.evaluation_detail, name='evaluation_detail'),
    path('evaluations/<int:pk>/modifier/', views.evaluation_update, name='evaluation_update'),
    path('evaluations/<int:pk>/supprimer/', views.evaluation_delete, name='evaluation_delete'),
    
    # APIs
    path('api/competences-section/', views.get_competences_section, name='get_competences_section'),
    path('api/eleves-section/', views.get_eleves_section, name='get_eleves_section'),
] 