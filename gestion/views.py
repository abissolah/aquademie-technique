from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import json
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import Adherent, Section, Competence, GroupeCompetence, Seance, Evaluation, LienEvaluation
from .forms import AdherentForm, SectionForm, CompetenceForm, GroupeCompetenceForm, SeanceForm, EvaluationBulkForm, UserRegistrationForm

# Vues d'accueil et de navigation
@login_required
def dashboard(request):
    """Tableau de bord principal"""
    context = {
        'total_adherents': Adherent.objects.count(),
        'total_seances': Seance.objects.count(),
        'seances_recentes': Seance.objects.all()[:5],
        'adherents_eleves': Adherent.objects.filter(statut='eleve').count(),
        'adherents_encadrants': Adherent.objects.filter(statut='encadrant').count(),
    }
    return render(request, 'gestion/dashboard.html', context)

# Vues pour les adhérents
class AdherentListView(LoginRequiredMixin, ListView):
    model = Adherent
    template_name = 'gestion/adherent_list.html'
    context_object_name = 'adherents'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Adherent.objects.all()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(email__icontains=q)
            )
        return queryset

class AdherentDetailView(LoginRequiredMixin, DetailView):
    model = Adherent
    template_name = 'gestion/adherent_detail.html'
    context_object_name = 'adherent'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context

class AdherentCreateView(LoginRequiredMixin, CreateView):
    model = Adherent
    form_class = AdherentForm
    template_name = 'gestion/adherent_form.html'
    success_url = reverse_lazy('adherent_list')

class AdherentUpdateView(LoginRequiredMixin, UpdateView):
    model = Adherent
    form_class = AdherentForm
    template_name = 'gestion/adherent_form.html'
    success_url = reverse_lazy('adherent_list')

class AdherentDeleteView(LoginRequiredMixin, DeleteView):
    model = Adherent
    template_name = 'gestion/adherent_confirm_delete.html'
    success_url = reverse_lazy('adherent_list')

# Vues pour les élèves
class EleveListView(LoginRequiredMixin, ListView):
    model = Adherent
    template_name = 'gestion/eleve_list.html'
    context_object_name = 'eleves'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Adherent.objects.filter(statut='eleve').order_by('nom', 'prenom')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(email__icontains=q)
            )
        return queryset

# Vues pour les encadrants
class EncadrantListView(LoginRequiredMixin, ListView):
    model = Adherent
    template_name = 'gestion/encadrant_list.html'
    context_object_name = 'encadrants'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Adherent.objects.filter(statut='encadrant').order_by('nom', 'prenom')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nom__icontains=q) | Q(prenom__icontains=q) | Q(email__icontains=q)
            )
        return queryset

# Vues pour les sections
class SectionListView(LoginRequiredMixin, ListView):
    model = Section
    template_name = 'gestion/section_list.html'
    context_object_name = 'sections'

class SectionDetailView(LoginRequiredMixin, DetailView):
    model = Section
    template_name = 'gestion/section_detail.html'
    context_object_name = 'section'

class SectionCreateView(LoginRequiredMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = 'gestion/section_form.html'
    success_url = reverse_lazy('section_list')

class SectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'gestion/section_form.html'
    success_url = reverse_lazy('section_list')

class SectionDeleteView(LoginRequiredMixin, DeleteView):
    model = Section
    template_name = 'gestion/section_confirm_delete.html'
    success_url = reverse_lazy('section_list')

# Vues pour les compétences
class CompetenceListView(LoginRequiredMixin, ListView):
    model = Competence
    template_name = 'gestion/competence_list.html'
    context_object_name = 'competences'
    
    def get_queryset(self):
        queryset = Competence.objects.select_related('section')
        section_id = self.request.GET.get('section')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sections'] = Section.objects.all()
        return context

class CompetenceCreateView(LoginRequiredMixin, CreateView):
    model = Competence
    form_class = CompetenceForm
    template_name = 'gestion/competence_form.html'
    success_url = reverse_lazy('competence_list')

class CompetenceUpdateView(LoginRequiredMixin, UpdateView):
    model = Competence
    form_class = CompetenceForm
    template_name = 'gestion/competence_form.html'
    success_url = reverse_lazy('competence_list')

# Vues pour les groupes de compétences
class GroupeCompetenceListView(LoginRequiredMixin, ListView):
    model = GroupeCompetence
    template_name = 'gestion/groupe_competence_list.html'
    context_object_name = 'groupes'

class GroupeCompetenceCreateView(LoginRequiredMixin, CreateView):
    model = GroupeCompetence
    form_class = GroupeCompetenceForm
    template_name = 'gestion/groupe_competence_form.html'
    success_url = reverse_lazy('groupe_competence_list')

class GroupeCompetenceUpdateView(LoginRequiredMixin, UpdateView):
    model = GroupeCompetence
    form_class = GroupeCompetenceForm
    template_name = 'gestion/groupe_competence_form.html'
    success_url = reverse_lazy('groupe_competence_list')

# Vues pour les séances
class SeanceListView(LoginRequiredMixin, ListView):
    model = Seance
    template_name = 'gestion/seance_list.html'
    context_object_name = 'seances'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Seance.objects.select_related('section', 'encadrant').prefetch_related('eleves', 'competences')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        section_id = self.request.GET.get('section')
        
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__lte=date_fin)
        if section_id:
            queryset = queryset.filter(section_id=section_id)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sections'] = Section.objects.all()
        return context

class SeanceDetailView(LoginRequiredMixin, DetailView):
    model = Seance
    template_name = 'gestion/seance_detail.html'
    context_object_name = 'seance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seance = self.get_object()
        
        # Récupérer le lien actif s'il existe
        lien_actif = seance.liens_evaluation.filter(est_valide=True).first()
        
        # Si pas de lien actif, récupérer le dernier lien généré (même s'il n'est plus actif)
        if not lien_actif:
            lien_actif = seance.liens_evaluation.order_by('-date_creation').first()
        
        # Récupérer tous les autres liens utilisés
        liens_utilises = seance.liens_evaluation.filter(est_valide=False).exclude(id=lien_actif.id if lien_actif else None)
        
        context['lien_actif'] = lien_actif
        context['liens_utilises'] = liens_utilises
        
        return context

class SeanceCreateView(LoginRequiredMixin, CreateView):
    model = Seance
    form_class = SeanceForm
    template_name = 'gestion/seance_form.html'
    success_url = reverse_lazy('seance_list')

class SeanceUpdateView(LoginRequiredMixin, UpdateView):
    model = Seance
    form_class = SeanceForm
    template_name = 'gestion/seance_form.html'
    success_url = reverse_lazy('seance_list')

class SeanceDeleteView(LoginRequiredMixin, DeleteView):
    model = Seance
    template_name = 'gestion/seance_confirm_delete.html'
    success_url = reverse_lazy('seance_list')

# Vues pour les évaluations
@login_required
def seance_evaluation(request, pk):
    """Page d'évaluation d'une séance"""
    seance = get_object_or_404(Seance, pk=pk)
    
    if request.method == 'POST':
        form = EvaluationBulkForm(seance, request.POST)
        if form.is_valid():
            # Sauvegarder les évaluations
            for eleve in seance.eleves.all():
                for competence in seance.competences.all():
                    note = form.cleaned_data.get(f'eval_{eleve.id}_{competence.id}')
                    commentaire = form.cleaned_data.get(f'comment_{eleve.id}_{competence.id}')
                    
                    if note is not None:
                        evaluation, created = Evaluation.objects.get_or_create(
                            seance=seance,
                            eleve=eleve,
                            competence=competence,
                            defaults={'note': note, 'commentaire': commentaire}
                        )
                        if not created:
                            evaluation.note = note
                            evaluation.commentaire = commentaire
                            evaluation.save()
            
            messages.success(request, 'Évaluations sauvegardées avec succès.')
            return redirect('seance_detail', pk=pk)
    else:
        form = EvaluationBulkForm(seance)
    
    context = {
        'seance': seance,
        'form': form,
    }
    return render(request, 'gestion/seance_evaluation.html', context)

@login_required
def seance_evaluation_view(request, pk):
    """Voir les évaluations d'une séance"""
    seance = get_object_or_404(Seance, pk=pk)
    evaluations = Evaluation.objects.filter(seance=seance).select_related('eleve', 'competence')
    
    # Organiser les évaluations par élève (liste d'évaluations)
    evaluations_par_eleve = {}
    for evaluation in evaluations:
        if evaluation.eleve not in evaluations_par_eleve:
            evaluations_par_eleve[evaluation.eleve] = []
        evaluations_par_eleve[evaluation.eleve].append(evaluation)
    
    context = {
        'seance': seance,
        'evaluations_par_eleve': evaluations_par_eleve,
    }
    return render(request, 'gestion/seance_evaluation_view.html', context)

# Vues pour les liens d'évaluation
@login_required
def generer_lien_evaluation(request, pk):
    """Générer un lien d'évaluation pour une séance"""
    seance = get_object_or_404(Seance, pk=pk)
    
    # Vérifier s'il existe déjà un lien valide pour cette séance
    lien_existant = LienEvaluation.objects.filter(seance=seance, est_valide=True).first()
    
    if lien_existant:
        # Marquer l'ancien lien comme utilisé
        lien_existant.est_valide = False
        lien_existant.save()
        messages.info(request, f'L\'ancien lien a été désactivé.')
    
    # Créer un nouveau lien d'évaluation
    lien = LienEvaluation.objects.create(
        seance=seance,
        date_expiration=timezone.now() + timedelta(days=30)  # Lien valide 30 jours
    )
    
    messages.success(request, f'Nouveau lien d\'évaluation généré : {request.build_absolute_uri(lien.url_evaluation)}')
    return redirect('seance_detail', pk=pk)

def evaluation_publique(request, token):
    """Page d'évaluation publique accessible sans connexion"""
    lien = get_object_or_404(LienEvaluation, token=token, est_valide=True)
    
    if timezone.now() > lien.date_expiration:
        messages.error(request, 'Ce lien d\'évaluation a expiré.')
        return render(request, 'gestion/evaluation_expiree.html')
    
    seance = lien.seance
    
    if request.method == 'POST':
        form = EvaluationBulkForm(seance, request.POST)
        if form.is_valid():
            # Sauvegarder les évaluations
            evaluations_sauvegardees = 0
            total_evaluations_attendues = seance.eleves.count() * seance.competences.count()
            
            for eleve in seance.eleves.all():
                for competence in seance.competences.all():
                    note = form.cleaned_data.get(f'eval_{eleve.id}_{competence.id}')
                    commentaire = form.cleaned_data.get(f'comment_{eleve.id}_{competence.id}')
                    
                    if note is not None:
                        evaluation, created = Evaluation.objects.get_or_create(
                            seance=seance,
                            eleve=eleve,
                            competence=competence,
                            defaults={'note': note, 'commentaire': commentaire}
                        )
                        if not created:
                            evaluation.note = note
                            evaluation.commentaire = commentaire
                            evaluation.save()
                        evaluations_sauvegardees += 1
            
            # Vérifier si toutes les évaluations ont été soumises
            if evaluations_sauvegardees == total_evaluations_attendues:
                # Toutes les évaluations sont complètes, marquer le lien comme utilisé
                lien.est_valide = False
                lien.save()
                messages.success(request, 'Toutes les évaluations ont été soumises avec succès. Le lien d\'évaluation est maintenant fermé.')
                return render(request, 'gestion/evaluation_soumise.html')
            else:
                # Évaluations partielles, garder le lien actif
                messages.success(request, f'{evaluations_sauvegardees}/{total_evaluations_attendues} évaluations sauvegardées. Vous pouvez continuer à évaluer les compétences restantes.')
                return redirect('evaluation_publique', token=token)
    else:
        form = EvaluationBulkForm(seance)
    
    # Charger les évaluations existantes pour pré-remplir le formulaire
    evaluations_existantes = {}
    for evaluation in Evaluation.objects.filter(seance=seance):
        key = f'eval_{evaluation.eleve.id}_{evaluation.competence.id}'
        evaluations_existantes[key] = evaluation.note
        
        key_comment = f'comment_{evaluation.eleve.id}_{evaluation.competence.id}'
        evaluations_existantes[key_comment] = evaluation.commentaire
    
    # Pré-remplir le formulaire avec les données existantes
    if evaluations_existantes:
        form = EvaluationBulkForm(seance, initial=evaluations_existantes)
    
    context = {
        'seance': seance,
        'form': form,
        'token': token,
    }
    return render(request, 'gestion/evaluation_publique.html', context)

# Vues pour la génération de PDF
@login_required
def generer_fiche_seance_pdf(request, pk):
    """Générer la fiche PDF d'une séance"""
    seance = get_object_or_404(Seance, pk=pk)
    
    # Créer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fiche_seance_{seance.date}_{seance.palanquee}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20
    )
    normal_style = styles['Normal']
    
    # Titre
    elements.append(Paragraph(f"Fiche de Séance - {seance.palanquee}", title_style))
    elements.append(Spacer(1, 20))
    
    # Informations générales
    elements.append(Paragraph("Informations générales", heading_style))
    elements.append(Paragraph(f"<b>Date :</b> {seance.date.strftime('%d/%m/%Y')}", normal_style))
    elements.append(Paragraph(f"<b>Encadrant :</b> {seance.encadrant.nom_complet}", normal_style))
    elements.append(Paragraph(f"<b>Section :</b> {seance.section.get_nom_display()}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Élèves
    elements.append(Paragraph("Élèves", heading_style))
    eleves_list = [eleve.nom_complet for eleve in seance.eleves.all()]
    elements.append(Paragraph(f"<b>Participants :</b> {', '.join(eleves_list)}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Compétences
    elements.append(Paragraph("Compétences", heading_style))
    competences_list = [competence.nom for competence in seance.competences.all()]
    for i, competence in enumerate(competences_list, 1):
        elements.append(Paragraph(f"{i}. {competence}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Précisions des exercices
    elements.append(Paragraph("Précisions des exercices", heading_style))
    elements.append(Paragraph(seance.precision_exercices, normal_style))
    
    # Construire le PDF
    doc.build(elements)
    return response

# Vues utilitaires
@login_required
def get_competences_section(request):
    """API pour récupérer les compétences d'une section (AJAX)"""
    section_id = request.GET.get('section_id')
    if section_id:
        competences = Competence.objects.filter(section_id=section_id).values('id', 'nom')
        return JsonResponse({'competences': list(competences)})
    return JsonResponse({'competences': []})

@login_required
def get_eleves_section(request):
    """API pour récupérer les élèves d'une section (AJAX)"""
    section_id = request.GET.get('section_id')
    if section_id:
        try:
            section = Section.objects.get(id=section_id)
            
            # D'abord, essayer de récupérer les élèves inscrits dans cette section
            eleves = Adherent.objects.filter(
                statut='eleve',
                sections=section
            ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
            
            # Si aucun élève n'est inscrit dans cette section, utiliser la logique de niveau
            if not eleves.exists():
                # Logique de filtrage des élèves selon la section (fallback)
                if section.nom == 'bapteme':
                    # Baptême : tous les élèves débutants
                    eleves = Adherent.objects.filter(
                        statut='eleve',
                        niveau='debutant'
                    ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
                elif section.nom == 'prepa_niveau1':
                    # Prépa Niveau 1 : débutants et niveau 1
                    eleves = Adherent.objects.filter(
                        statut='eleve',
                        niveau__in=['debutant', 'niveau1']
                    ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
                elif section.nom == 'prepa_niveau2':
                    # Prépa Niveau 2 : niveau 1 et niveau 2
                    eleves = Adherent.objects.filter(
                        statut='eleve',
                        niveau__in=['niveau1', 'niveau2']
                    ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
                elif section.nom == 'prepa_niveau3':
                    # Prépa Niveau 3 : niveau 2 et niveau 3
                    eleves = Adherent.objects.filter(
                        statut='eleve',
                        niveau__in=['niveau2', 'niveau3']
                    ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
                elif section.nom == 'prepa_niveau4':
                    # Prépa Niveau 4 : niveau 3
                    eleves = Adherent.objects.filter(
                        statut='eleve',
                        niveau='niveau3'
                    ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
                elif section.nom == 'niveau3':
                    # Niveau 3 : niveau 3
                    eleves = Adherent.objects.filter(
                        statut='eleve',
                        niveau='niveau3'
                    ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
                elif section.nom == 'niveau4':
                    # Niveau 4 : niveau 3 et plus
                    eleves = Adherent.objects.filter(
                        statut='eleve',
                        niveau__in=['niveau3', 'initiateur1', 'initiateur2', 'moniteur_federal1', 'moniteur_federal2']
                    ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
                elif section.nom == 'encadrant':
                    # Encadrant : initiateurs et moniteurs
                    eleves = Adherent.objects.filter(
                        statut='eleve',
                        niveau__in=['initiateur1', 'initiateur2', 'moniteur_federal1', 'moniteur_federal2']
                    ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
                else:
                    # Par défaut : tous les élèves
                    eleves = Adherent.objects.filter(
                        statut='eleve'
                    ).values('id', 'nom', 'prenom').order_by('nom', 'prenom')
            
            return JsonResponse({'eleves': list(eleves)})
        except Section.DoesNotExist:
            return JsonResponse({'eleves': []})
    return JsonResponse({'eleves': []})



# Vues d'authentification personnalisées
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'login'
