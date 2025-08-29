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

from .models import Adherent, Section, Competence, GroupeCompetence, Seance, Evaluation, LienEvaluation, Palanquee
from .forms import AdherentForm, SectionForm, CompetenceForm, GroupeCompetenceForm, SeanceForm, EvaluationBulkForm, PalanqueeForm
from .utils import envoyer_lien_evaluation, envoyer_lien_evaluation_avec_cc

# Vues d'accueil et de navigation
@login_required
def dashboard(request):
    """Tableau de bord principal"""
    context = {
        'total_adherents': Adherent.objects.count(),
        'total_seances': Seance.objects.count(),
        'total_palanquees': Palanquee.objects.count(),
        'seances_recentes': Seance.objects.all()[:5],
        'palanquees_recentes': Palanquee.objects.select_related('seance', 'section').prefetch_related('eleves')[:5],
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

class CompetenceDeleteView(LoginRequiredMixin, DeleteView):
    model = Competence
    template_name = 'gestion/competence_confirm_delete.html'
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

class GroupeCompetenceDeleteView(LoginRequiredMixin, DeleteView):
    model = GroupeCompetence
    template_name = 'gestion/groupe_competence_confirm_delete.html'
    success_url = reverse_lazy('groupe_competence_list')

# Vues pour les séances
class SeanceListView(LoginRequiredMixin, ListView):
    model = Seance
    template_name = 'gestion/seance_list.html'
    context_object_name = 'seances'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Seance.objects.prefetch_related('palanquees')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__lte=date_fin)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class SeanceDetailView(LoginRequiredMixin, DetailView):
    model = Seance
    template_name = 'gestion/seance_detail.html'
    context_object_name = 'seance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seance = self.get_object()
        
        # Récupérer les palanquées associées
        context['palanquees'] = seance.palanquees.all()
        
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
def evaluation_detail(request, pk):
    """Voir le détail d'une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=pk)
    return render(request, 'gestion/evaluation_detail.html', {'evaluation': evaluation})

@login_required
def evaluation_update(request, pk):
    """Modifier une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=pk)
    
    if request.method == 'POST':
        form = EvaluationBulkForm(evaluation.palanquee, request.POST)
        if form.is_valid():
            # Sauvegarder l'évaluation
            note = form.cleaned_data.get(f'eval_{evaluation.eleve.id}_{evaluation.competence.id}')
            commentaire = form.cleaned_data.get(f'comment_{evaluation.eleve.id}_{evaluation.competence.id}')
            
            if note is not None:
                evaluation.note = note
                evaluation.commentaire = commentaire
                evaluation.save()
                messages.success(request, 'Évaluation mise à jour avec succès.')
                return redirect('palanquee_detail', pk=evaluation.palanquee.pk)
    else:
        form = EvaluationBulkForm(evaluation.palanquee)
    
    context = {
        'evaluation': evaluation,
        'form': form,
    }
    return render(request, 'gestion/evaluation_update.html', context)

@login_required
def evaluation_delete(request, pk):
    """Supprimer une évaluation"""
    evaluation = get_object_or_404(Evaluation, pk=pk)
    palanquee_pk = evaluation.palanquee.pk
    
    if request.method == 'POST':
        evaluation.delete()
        messages.success(request, 'Évaluation supprimée avec succès.')
        return redirect('palanquee_detail', pk=palanquee_pk)
    
    return render(request, 'gestion/evaluation_confirm_delete.html', {'evaluation': evaluation})

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

# Vues pour l'import Excel
@login_required
def import_adherents_excel(request):
    """Import en masse d'adhérents depuis un fichier Excel"""
    if request.method == 'POST':
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            
            # Vérifier l'extension du fichier
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'Veuillez sélectionner un fichier Excel (.xlsx ou .xls)')
                return render(request, 'gestion/import_adherents_excel.html')
            
            try:
                import pandas as pd
                from datetime import datetime
                import re
                
                # Lire le fichier Excel
                if excel_file.name.endswith('.xlsx'):
                    df = pd.read_excel(excel_file, engine='openpyxl')
                else:
                    df = pd.read_excel(excel_file, engine='xlrd')
                
                # Vérifier les colonnes requises
                required_columns = ['nom', 'prenom', 'date_naissance', 'adresse', 'email', 
                                  'telephone', 'date_fin_validite_caci', 'niveau', 'statut']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    messages.error(request, f'Colonnes manquantes dans le fichier : {", ".join(missing_columns)}')
                    return render(request, 'gestion/import_adherents_excel.html')
                
                # Valeurs autorisées pour la validation
                niveaux_valides = ['debutant', 'niveau1', 'niveau2', 'niveau3', 'initiateur1', 'initiateur2', 'moniteur_federal1', 'moniteur_federal2']
                statuts_valides = ['eleve', 'encadrant']
                
                # Traitement des données
                success_count = 0
                error_count = 0
                errors = []
                imported_adherents = []
                
                for index, row in df.iterrows():
                    try:
                        # Nettoyer les données
                        nom = str(row['nom']).strip() if pd.notna(row['nom']) else ''
                        prenom = str(row['prenom']).strip() if pd.notna(row['prenom']) else ''
                        email = str(row['email']).strip() if pd.notna(row['email']) else ''
                        
                        # Vérifier les champs obligatoires
                        if not nom or not prenom or not email:
                            errors.append(f"Ligne {index + 2}: nom, prénom et email sont obligatoires")
                            error_count += 1
                            continue
                        
                        # Vérifier si l'adhérent existe déjà (email OU nom+prénom)
                        if Adherent.objects.filter(email=email).exists():
                            errors.append(f"Ligne {index + 2}: l'email {email} existe déjà")
                            error_count += 1
                            continue
                        
                        if Adherent.objects.filter(nom=nom, prenom=prenom).exists():
                            errors.append(f"Ligne {index + 2}: l'adhérent {nom} {prenom} existe déjà")
                            error_count += 1
                            continue
                        
                        # Validation du format des dates (DD/MM/YYYY uniquement)
                        date_naissance = None
                        date_fin_validite_caci = None
                        
                        # Validation date de naissance
                        if pd.notna(row['date_naissance']):
                            date_str = str(row['date_naissance']).strip()
                            if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                                try:
                                    date_naissance = datetime.strptime(date_str, '%d/%m/%Y').date()
                                except ValueError:
                                    errors.append(f"Ligne {index + 2}: date de naissance '{date_str}' invalide (format DD/MM/YYYY attendu)")
                                    error_count += 1
                                    continue
                            else:
                                errors.append(f"Ligne {index + 2}: date de naissance '{date_str}' format incorrect (DD/MM/YYYY attendu)")
                                error_count += 1
                                continue
                        else:
                            date_naissance = datetime.now().date()
                        
                        # Validation date fin validité CACI
                        if pd.notna(row['date_fin_validite_caci']):
                            date_str = str(row['date_fin_validite_caci']).strip()
                            if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                                try:
                                    date_fin_validite_caci = datetime.strptime(date_str, '%d/%m/%Y').date()
                                except ValueError:
                                    errors.append(f"Ligne {index + 2}: date fin validité CACI '{date_str}' invalide (format DD/MM/YYYY attendu)")
                                    error_count += 1
                                    continue
                            else:
                                errors.append(f"Ligne {index + 2}: date fin validité CACI '{date_str}' format incorrect (DD/MM/YYYY attendu)")
                                error_count += 1
                                continue
                        else:
                            date_fin_validite_caci = datetime.now().date()
                        
                        # Validation du niveau
                        niveau = str(row['niveau']).strip() if pd.notna(row['niveau']) else 'debutant'
                        if niveau not in niveaux_valides:
                            errors.append(f"Ligne {index + 2}: niveau '{niveau}' invalide (valeurs: {', '.join(niveaux_valides)})")
                            error_count += 1
                            continue
                        
                        # Validation du statut
                        statut = str(row['statut']).strip() if pd.notna(row['statut']) else 'eleve'
                        if statut not in statuts_valides:
                            errors.append(f"Ligne {index + 2}: statut '{statut}' invalide (valeurs: {', '.join(statuts_valides)})")
                            error_count += 1
                            continue
                        
                        # Validation des sections
                        sections_invalides = []
                        if 'sections' in df.columns and pd.notna(row['sections']):
                            sections_str = str(row['sections']).strip()
                            if sections_str:
                                section_names = [s.strip() for s in sections_str.split(',')]
                                for section_name in section_names:
                                    if not Section.objects.filter(nom=section_name).exists():
                                        sections_invalides.append(section_name)
                        
                        if sections_invalides:
                            errors.append(f"Ligne {index + 2}: sections inexistantes: {', '.join(sections_invalides)}")
                            error_count += 1
                            continue
                        
                        # Si toutes les validations passent, créer l'adhérent
                        adherent = Adherent.objects.create(
                            nom=nom,
                            prenom=prenom,
                            date_naissance=date_naissance,
                            adresse=str(row['adresse']).strip() if pd.notna(row['adresse']) else '',
                            email=email,
                            telephone=str(row['telephone']).strip() if pd.notna(row['telephone']) else '',
                            date_fin_validite_caci=date_fin_validite_caci,
                            niveau=niveau,
                            statut=statut,
                        )
                        
                        # Ajouter les sections
                        if 'sections' in df.columns and pd.notna(row['sections']):
                            sections_str = str(row['sections']).strip()
                            if sections_str:
                                section_names = [s.strip() for s in sections_str.split(',')]
                                for section_name in section_names:
                                    try:
                                        section = Section.objects.get(nom=section_name)
                                        adherent.sections.add(section)
                                    except Section.DoesNotExist:
                                        pass
                        
                        success_count += 1
                        imported_adherents.append(f"{nom} {prenom}")
                        
                    except Exception as e:
                        errors.append(f"Ligne {index + 2}: {str(e)}")
                        error_count += 1
                
                # Stocker les résultats dans la session pour l'affichage
                request.session['import_results'] = {
                    'success_count': success_count,
                    'error_count': error_count,
                    'errors': errors,
                    'imported_adherents': imported_adherents
                }
                
                # Messages de résultat
                if success_count > 0:
                    messages.success(request, f'{success_count} adhérent(s) importé(s) avec succès')
                
                if error_count > 0:
                    messages.warning(request, f'{error_count} erreur(s) lors de l\'import')
                
                return render(request, 'gestion/import_adherents_excel.html')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la lecture du fichier Excel : {str(e)}')
                return render(request, 'gestion/import_adherents_excel.html')
        else:
            messages.error(request, 'Aucun fichier sélectionné')
            return render(request, 'gestion/import_adherents_excel.html')
    
    # Affichage de la page d'import (GET request)
    return render(request, 'gestion/import_adherents_excel.html')

@login_required
def download_excel_template(request):
    """Télécharger le modèle Excel pour l'import d'adhérents"""
    import pandas as pd
    from datetime import date, timedelta
    
    # Créer un DataFrame d'exemple
    data = {
        'nom': ['Dupont', 'Martin', 'Bernard'],
        'prenom': ['Jean', 'Marie', 'Pierre'],
        'date_naissance': ['15/05/1990', '03/12/1985', '22/08/1992'],
        'adresse': ['123 Rue de la Paix, Paris', '456 Avenue des Champs, Lyon', '789 Boulevard de la Mer, Nice'],
        'email': ['jean.dupont@email.com', 'marie.martin@email.com', 'pierre.bernard@email.com'],
        'telephone': ['0123456789', '0987654321', '0567891234'],
        'date_fin_validite_caci': ['31/12/2025', '30/06/2026', '15/09/2025'],
        'niveau': ['niveau1', 'niveau2', 'debutant'],
        'statut': ['eleve', 'eleve', 'eleve'],
        'sections': ['bapteme,prepa_niveau1', 'prepa_niveau2', 'bapteme']
    }
    
    df = pd.DataFrame(data)
    
    # Créer la réponse HTTP
    from django.http import HttpResponse
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="modele_import_adherents.xlsx"'
    
    # Écrire le fichier Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Adhérents', index=False)
        
        # Ajouter une feuille avec les instructions
        instructions = pd.DataFrame({
            'Colonne': ['nom', 'prenom', 'date_naissance', 'adresse', 'email', 'telephone', 'date_fin_validite_caci', 'niveau', 'statut', 'sections'],
            'Description': [
                'Nom de famille (obligatoire)',
                'Prénom (obligatoire)',
                'Date de naissance (format: DD/MM/YYYY)',
                'Adresse complète',
                'Email (obligatoire, unique)',
                'Numéro de téléphone',
                'Date de fin de validité CACI (format: DD/MM/YYYY)',
                'Niveau de plongée (debutant, niveau1, niveau2, niveau3, initiateur1, initiateur2, moniteur_federal1, moniteur_federal2)',
                'Statut (eleve ou encadrant)',
                'Sections (séparées par des virgules: bapteme,prepa_niveau1,prepa_niveau2)'
            ],
            'Obligatoire': ['Oui', 'Oui', 'Non', 'Non', 'Oui', 'Non', 'Non', 'Non', 'Non', 'Non'],
            'Exemple': ['Dupont', 'Jean', '15/05/1990', '123 Rue de la Paix, Paris', 'jean.dupont@email.com', '0123456789', '31/12/2025', 'niveau1', 'eleve', 'bapteme,prepa_niveau1']
        })
        
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
    
    return response

# Vues d'authentification personnalisées
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'login'

