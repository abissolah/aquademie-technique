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
    path('adherents/export-excel/', views.export_adherents_excel, name='export_adherents_excel'),
    path('adherents/inscription/', views.AdherentPublicCreateView.as_view(), name='adherent_public_create'),
    path('adherents/inscription/success/', views.dashboard, name='adherent_public_success'),
    path('adherents/<int:adherent_id>/valider-caci/', views.valider_caci, name='valider_caci'),
    
    # Élèves
    path('eleves/', views.EleveListView.as_view(), name='eleve_list'),
    path('eleves/<int:eleve_id>/suivi-formation/', views.suivi_formation_eleve, name='suivi_formation_eleve'),
    
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
    path('competences/<int:pk>/', views.CompetenceDetailView.as_view(), name='competence_detail'),
    
    # Groupes de compétences
    path('groupes-competences/', views.GroupeCompetenceListView.as_view(), name='groupe_competence_list'),
    path('groupes-competences/nouveau/', views.GroupeCompetenceCreateView.as_view(), name='groupe_competence_create'),
    path('groupes-competences/<int:pk>/modifier/', views.GroupeCompetenceUpdateView.as_view(), name='groupe_competence_update'),
    path('groupes-competences/<int:pk>/supprimer/', views.GroupeCompetenceDeleteView.as_view(), name='groupe_competence_delete'),
    path('groupes-competences/<int:pk>/', views.GroupeCompetenceDetailView.as_view(), name='groupe_competence_detail'),
    
    # Séances
    path('seances/', views.SeanceListView.as_view(), name='seance_list'),
    path('seances/<int:pk>/', views.SeanceDetailView.as_view(), name='seance_detail'),
    path('seances/nouvelle/', views.SeanceCreateView.as_view(), name='seance_create'),
    path('seances/<int:pk>/modifier/', views.SeanceUpdateView.as_view(), name='seance_update'),
    path('seances/<int:pk>/supprimer/', views.SeanceDeleteView.as_view(), name='seance_delete'),
    path('seances/<int:seance_id>/generer-lien-inscription/', views.generer_lien_inscription_seance, name='generer_lien_inscription_seance'),
    path('seances/<int:seance_id>/envoyer-invitation/', views.envoyer_mail_invitation_seance, name='envoyer_mail_invitation_seance'),
    path('seances/<int:seance_id>/exporter-inscrits/', views.exporter_inscrits_seance, name='exporter_inscrits_seance'),
    path('seances/<int:seance_id>/exporter-covoiturage/', views.exporter_covoiturage_seance, name='exporter_covoiturage_seance'),
    path('seances/<int:seance_id>/importer-palanquees/', views.importer_palanquees_seance, name='importer_palanquees_seance'),
    path('seances/<int:seance_id>/creer-palanquees/', views.creer_palanquees, name='creer_palanquees'),
    path('seances/<int:seance_id>/fiche-securite/', views.generer_fiche_securite, name='generer_fiche_securite'),
    path('seances/<int:seance_id>/fiche-securite-excel/', views.generer_fiche_securite_excel, name='generer_fiche_securite_excel'),
    path('seances/<int:seance_id>/admin-inscription/', views.admin_inscription_seance, name='admin_inscription_seance'),
    path('seances/<int:seance_id>/envoyer-pdf-palanquees/', views.envoyer_pdf_palanquees_encadrants, name='envoyer_pdf_palanquees_encadrants'),
    path('seances/<int:seance_id>/envoyer-mail-covoiturage/', views.envoyer_mail_covoiturage, name='envoyer_mail_covoiturage'),
    
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
    
    # Lieux
    path('lieux/', views.LieuListView.as_view(), name='lieu_list'),
    path('lieux/nouveau/', views.LieuCreateView.as_view(), name='lieu_create'),
    path('lieux/<int:pk>/modifier/', views.LieuUpdateView.as_view(), name='lieu_update'),
    path('lieux/<int:pk>/supprimer/', views.LieuDeleteView.as_view(), name='lieu_delete'),
    
    # Exercices
    path('exercices/', views.ExerciceListView.as_view(), name='exercice_list'),
    path('exercices/nouveau/', views.ExerciceCreateView.as_view(), name='exercice_create'),
    path('exercices/<int:pk>/modifier/', views.ExerciceUpdateView.as_view(), name='exercice_update'),
    path('exercices/<int:pk>/supprimer/', views.ExerciceDeleteView.as_view(), name='exercice_delete'),
    
    # APIs
    path('api/competences-section/', views.get_competences_section, name='get_competences_section'),
    path('api/eleves-section/', views.get_eleves_section, name='get_eleves_section'),
    path('api/dupliquer-exercices-palanquee/', views.dupliquer_exercices_palanquee, name='dupliquer_exercices_palanquee'),
    path('inscription/<uuid:uuid>/', views.inscription_seance_uuid, name='inscription_seance_uuid'),
    path('api/membres-app/', views.api_membres_app, name='api_membres_app'),
    path('api/inscrire-membre-app/', views.api_inscrire_membre_app, name='api_inscrire_membre_app'),
    path('api/recherche-non-membre/', views.api_recherche_non_membre, name='api_recherche_non_membre'),
    path('api/inscrire-non-membre/', views.api_inscrire_non_membre, name='api_inscrire_non_membre'),
    path('inscription/<int:inscription_id>/supprimer/', views.supprimer_inscription_seance, name='supprimer_inscription_seance'),
    path('envoyer-mail-inscription/', views.envoyer_mail_inscription, name='envoyer_mail_inscription'),
] 