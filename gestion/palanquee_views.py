from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from .models import Palanquee, Evaluation, LienEvaluation
from .forms import PalanqueeForm, EvaluationBulkForm

# Vues pour les palanquées
class PalanqueeListView(LoginRequiredMixin, ListView):
    model = Palanquee
    template_name = 'gestion/palanquee_list.html'
    context_object_name = 'palanquees'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Palanquee.objects.select_related('seance', 'section', 'encadrant').prefetch_related('eleves', 'competences')
        section_id = self.request.GET.get('section')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        if date_debut:
            queryset = queryset.filter(seance__date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(seance__date__lte=date_fin)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Section
        context['sections'] = Section.objects.all()
        return context

class PalanqueeDetailView(LoginRequiredMixin, DetailView):
    model = Palanquee
    template_name = 'gestion/palanquee_detail.html'
    context_object_name = 'palanquee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        palanquee = self.get_object()
        
        # Récupérer le lien actif s'il existe
        lien_actif = palanquee.liens_evaluation.filter(est_valide=True).first()
        
        # Si pas de lien actif, récupérer le dernier lien généré (même s'il n'est plus actif)
        if not lien_actif:
            lien_actif = palanquee.liens_evaluation.order_by('-date_creation').first()
        
        # Récupérer tous les autres liens utilisés
        liens_utilises = palanquee.liens_evaluation.filter(est_valide=False).exclude(id=lien_actif.id if lien_actif else None)
        
        context['lien_actif'] = lien_actif
        context['liens_utilises'] = liens_utilises
        
        return context

class PalanqueeCreateView(LoginRequiredMixin, CreateView):
    model = Palanquee
    form_class = PalanqueeForm
    template_name = 'gestion/palanquee_form.html'
    success_url = reverse_lazy('palanquee_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Récupérer l'ID de la séance depuis les paramètres GET
        seance_id = self.request.GET.get('seance')
        if seance_id:
            kwargs['seance_id'] = seance_id
        return kwargs
    
    def form_valid(self, form):
        # Mettre à jour le queryset des compétences avant la validation
        section = form.cleaned_data.get('section')
        if section:
            form.fields['competences'].queryset = form.fields['competences'].queryset.filter(section=section)
        response = super().form_valid(form)
        messages.success(self.request, 'Palanquée créée avec succès.')
        return response
    
    def get_success_url(self):
        # Rediriger vers la séance si elle était spécifiée
        seance_id = self.request.GET.get('seance')
        if seance_id:
            return reverse_lazy('seance_update', kwargs={'pk': seance_id})
        return super().get_success_url()

class PalanqueeUpdateView(LoginRequiredMixin, UpdateView):
    model = Palanquee
    form_class = PalanqueeForm
    template_name = 'gestion/palanquee_form.html'
    success_url = reverse_lazy('palanquee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        palanquee = self.object
        seance = palanquee.seance
        from gestion.models import InscriptionSeance, PalanqueeEleve
        eleves_seance = [i.personne for i in InscriptionSeance.objects.filter(seance=seance).select_related('personne') if i.personne.statut == 'eleve']
        eleves_palanquee = list(palanquee.eleves.all())
        eleves_aptitudes = {}
        for e in eleves_palanquee:
            pe = PalanqueeEleve.objects.filter(palanquee=palanquee, eleve=e).first()
            eleves_aptitudes[e.id] = pe.aptitude if pe else ''
        # Prépare une liste de tuples (eleve, aptitude)
        eleves_seance_aptitudes = [(eleve, eleves_aptitudes.get(eleve.id, '')) for eleve in eleves_seance]
        context['eleves_seance_aptitudes'] = eleves_seance_aptitudes
        context['eleves_palanquee'] = eleves_palanquee
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        palanquee = self.object
        from gestion.models import PalanqueeEleve
        eleves_ids = self.request.POST.getlist('eleves_in_palanquee')
        # Supprime les liens non cochés
        PalanqueeEleve.objects.filter(palanquee=palanquee).exclude(eleve_id__in=eleves_ids).delete()
        # Ajoute ou met à jour les liens cochés et leur aptitude
        for eid in eleves_ids:
            aptitude = self.request.POST.get(f'aptitude_{eid}', '').strip()
            pe, created = PalanqueeEleve.objects.get_or_create(palanquee=palanquee, eleve_id=eid)
            pe.aptitude = aptitude
            pe.save()
        return response
    
    def get_success_url(self):
        # Rediriger vers la séance associée
        return reverse_lazy('seance_update', kwargs={'pk': self.object.seance.pk})

class PalanqueeDeleteView(LoginRequiredMixin, DeleteView):
    model = Palanquee
    template_name = 'gestion/palanquee_confirm_delete.html'
    
    def get_success_url(self):
        # Rediriger vers la séance associée
        return reverse_lazy('seance_update', kwargs={'pk': self.object.seance.pk})

# Vues pour les évaluations des palanquées
@login_required
def palanquee_evaluation(request, pk):
    """Page d'évaluation d'une palanquée"""
    palanquee = get_object_or_404(Palanquee, pk=pk)
    
    if request.method == 'POST':
        form = EvaluationBulkForm(palanquee, request.POST)
        if form.is_valid():
            # Sauvegarder les évaluations
            for eleve in palanquee.eleves.all():
                for competence in palanquee.competences.all():
                    note = form.cleaned_data.get(f'eval_{eleve.id}_{competence.id}')
                    commentaire = form.cleaned_data.get(f'comment_{eleve.id}_{competence.id}')
                    
                    if note is not None:
                        evaluation, created = Evaluation.objects.get_or_create(
                            palanquee=palanquee,
                            eleve=eleve,
                            competence=competence,
                            defaults={'note': note, 'commentaire': commentaire}
                        )
                        if not created:
                            evaluation.note = note
                            evaluation.commentaire = commentaire
                            evaluation.save()
            
            messages.success(request, 'Évaluations sauvegardées avec succès.')
            return redirect('palanquee_detail', pk=pk)
    else:
        form = EvaluationBulkForm(palanquee)
    
    context = {
        'palanquee': palanquee,
        'form': form,
    }
    return render(request, 'gestion/palanquee_evaluation.html', context)

@login_required
def palanquee_evaluation_view(request, pk):
    """Voir les évaluations d'une palanquée"""
    palanquee = get_object_or_404(Palanquee, pk=pk)
    evaluations = Evaluation.objects.filter(palanquee=palanquee).select_related('eleve', 'competence')
    
    # Organiser les évaluations par élève (liste d'évaluations)
    evaluations_par_eleve = {}
    for evaluation in evaluations:
        if evaluation.eleve not in evaluations_par_eleve:
            evaluations_par_eleve[evaluation.eleve] = []
        evaluations_par_eleve[evaluation.eleve].append(evaluation)
    
    context = {
        'palanquee': palanquee,
        'evaluations_par_eleve': evaluations_par_eleve,
    }
    return render(request, 'gestion/palanquee_evaluation_view.html', context)

# Vues pour les liens d'évaluation
@login_required
def generer_lien_evaluation(request, pk):
    """Générer un lien d'évaluation pour une palanquée"""
    palanquee = get_object_or_404(Palanquee, pk=pk)
    
    # Vérifier s'il existe déjà un lien valide pour cette palanquée
    lien_existant = LienEvaluation.objects.filter(palanquee=palanquee, est_valide=True).first()
    
    if lien_existant:
        # Marquer l'ancien lien comme utilisé
        lien_existant.est_valide = False
        lien_existant.save()
        messages.info(request, f'L\'ancien lien a été désactivé.')
    
    # Créer un nouveau lien d'évaluation
    lien = LienEvaluation.objects.create(
        palanquee=palanquee,
        date_expiration=timezone.now() + timedelta(days=30)  # Lien valide 30 jours
    )
    
    messages.success(request, f'Nouveau lien d\'évaluation généré : {request.build_absolute_uri(lien.url_evaluation)}')
    return redirect('palanquee_detail', pk=pk)

def evaluation_publique(request, token):
    """Page d'évaluation publique accessible sans connexion"""
    lien = get_object_or_404(LienEvaluation, token=token, est_valide=True)
    
    if timezone.now() > lien.date_expiration:
        messages.error(request, 'Ce lien d\'évaluation a expiré.')
        return render(request, 'gestion/evaluation_expiree.html')
    
    palanquee = lien.palanquee
    
    if request.method == 'POST':
        form = EvaluationBulkForm(palanquee, request.POST)
        if form.is_valid():
            # Sauvegarder les évaluations
            evaluations_sauvegardees = 0
            total_evaluations_attendues = palanquee.eleves.count() * palanquee.competences.count()
            
            for eleve in palanquee.eleves.all():
                for competence in palanquee.competences.all():
                    note = form.cleaned_data.get(f'eval_{eleve.id}_{competence.id}')
                    commentaire = form.cleaned_data.get(f'comment_{eleve.id}_{competence.id}')
                    
                    if note is not None:
                        evaluation, created = Evaluation.objects.get_or_create(
                            palanquee=palanquee,
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
        form = EvaluationBulkForm(palanquee)
    
    # Charger les évaluations existantes pour pré-remplir le formulaire
    evaluations_existantes = {}
    for evaluation in Evaluation.objects.filter(palanquee=palanquee):
        key = f'eval_{evaluation.eleve.id}_{evaluation.competence.id}'
        evaluations_existantes[key] = evaluation.note
        
        key_comment = f'comment_{evaluation.eleve.id}_{evaluation.competence.id}'
        evaluations_existantes[key_comment] = evaluation.commentaire
    
    # Pré-remplir le formulaire avec les données existantes
    if evaluations_existantes:
        form = EvaluationBulkForm(palanquee, initial=evaluations_existantes)
    
    context = {
        'palanquee': palanquee,
        'form': form,
        'token': token,
    }
    return render(request, 'gestion/evaluation_publique.html', context)

# Vues pour la génération de PDF
@login_required
def generer_fiche_palanquee_pdf(request, pk):
    """Générer la fiche PDF d'une palanquée"""
    palanquee = get_object_or_404(Palanquee, pk=pk)
    
    # Créer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fiche_palanquee_{palanquee.seance.date}_{palanquee.section.get_nom_display()}.pdf"'
    
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
    elements.append(Paragraph(f"Fiche de Palanquée - {palanquee.section.get_nom_display()}", title_style))
    elements.append(Spacer(1, 20))
    
    # Informations générales
    elements.append(Paragraph("Informations générales", heading_style))
    elements.append(Paragraph(f"<b>Date :</b> {palanquee.seance.date.strftime('%d/%m/%Y')}", normal_style))
    elements.append(Paragraph(f"<b>Lieu :</b> {palanquee.seance.lieu}", normal_style))
    elements.append(Paragraph(f"<b>Encadrant :</b> {palanquee.encadrant.nom_complet}", normal_style))
    elements.append(Paragraph(f"<b>Section :</b> {palanquee.section.get_nom_display()}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Élèves
    elements.append(Paragraph("Élèves", heading_style))
    eleves_list = [eleve.nom_complet for eleve in palanquee.eleves.all()]
    elements.append(Paragraph(f"<b>Participants :</b> {', '.join(eleves_list)}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Compétences
    elements.append(Paragraph("Compétences", heading_style))
    competences_list = [competence.nom for competence in palanquee.competences.all()]
    for i, competence in enumerate(competences_list, 1):
        elements.append(Paragraph(f"{i}. {competence}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Précisions des exercices
    if palanquee.precision_exercices:
        elements.append(Paragraph("Précisions des exercices", heading_style))
        elements.append(Paragraph(palanquee.precision_exercices, normal_style))
    
    # Construire le PDF
    doc.build(elements)
    return response

# Vues utilitaires
@login_required
def envoyer_lien_par_email(request, pk):
    """Envoyer le lien d'évaluation par email à l'encadrant"""
    palanquee = get_object_or_404(Palanquee, pk=pk)
    
    # Récupérer le lien actif
    lien_actif = palanquee.liens_evaluation.filter(est_valide=True).first()
    
    if not lien_actif:
        # Si pas de lien actif, récupérer le dernier lien généré
        lien_actif = palanquee.liens_evaluation.order_by('-date_creation').first()
    
    if not lien_actif:
        messages.error(request, 'Aucun lien d\'évaluation trouvé pour cette palanquée.')
        return redirect('palanquee_detail', pk=pk)
    
    # Vérifier que l'encadrant a une adresse email
    if not palanquee.encadrant.email:
        messages.error(request, f'L\'encadrant {palanquee.encadrant.nom_complet} n\'a pas d\'adresse email configurée.')
        return redirect('palanquee_detail', pk=pk)
    
    # Envoyer l'email
    from .utils import envoyer_lien_evaluation
    success, message = envoyer_lien_evaluation(lien_actif, request)
    
    if success:
        messages.success(request, f'Lien d\'évaluation envoyé avec succès à {palanquee.encadrant.email}')
    else:
        messages.error(request, message)
    
    return redirect('palanquee_detail', pk=pk)
