from django.urls import path
from . import views

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
    
    # Élèves
    path('eleves/', views.EleveListView.as_view(), name='eleve_list'),
    
    # Encadrants
    path('encadrants/', views.EncadrantListView.as_view(), name='encadrant_list'),
    
    # Sections
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/<int:pk>/', views.SectionDetailView.as_view(), name='section_detail'),
    path('sections/nouvelle/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<int:pk>/modifier/', views.SectionUpdateView.as_view(), name='section_update'),
    
    # Compétences
    path('competences/', views.CompetenceListView.as_view(), name='competence_list'),
    path('competences/nouvelle/', views.CompetenceCreateView.as_view(), name='competence_create'),
    path('competences/<int:pk>/modifier/', views.CompetenceUpdateView.as_view(), name='competence_update'),
    
    # Groupes de compétences
    path('groupes-competences/', views.GroupeCompetenceListView.as_view(), name='groupe_competence_list'),
    path('groupes-competences/nouveau/', views.GroupeCompetenceCreateView.as_view(), name='groupe_competence_create'),
    path('groupes-competences/<int:pk>/modifier/', views.GroupeCompetenceUpdateView.as_view(), name='groupe_competence_update'),
    
    # Séances
    path('seances/', views.SeanceListView.as_view(), name='seance_list'),
    path('seances/<int:pk>/', views.SeanceDetailView.as_view(), name='seance_detail'),
    path('seances/nouvelle/', views.SeanceCreateView.as_view(), name='seance_create'),
    path('seances/<int:pk>/modifier/', views.SeanceUpdateView.as_view(), name='seance_update'),
    path('seances/<int:pk>/supprimer/', views.SeanceDeleteView.as_view(), name='seance_delete'),
    
    # Évaluations
    path('seances/<int:pk>/evaluation/', views.seance_evaluation, name='seance_evaluation'),
    path('seances/<int:pk>/evaluation/voir/', views.seance_evaluation_view, name='seance_evaluation_view'),
    
    # Liens d'évaluation
    path('seances/<int:pk>/generer-lien/', views.generer_lien_evaluation, name='generer_lien_evaluation'),
    path('evaluation/<uuid:token>/', views.evaluation_publique, name='evaluation_publique'),
    
    # PDF
    path('seances/<int:pk>/pdf/', views.generer_fiche_seance_pdf, name='generer_fiche_seance_pdf'),
    
    # API
    path('api/competences-section/', views.get_competences_section, name='get_competences_section'),
    
    # Authentification
    path('register/', views.register, name='register'),
] 