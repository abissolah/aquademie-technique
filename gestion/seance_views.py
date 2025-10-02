from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from .models import Seance, Section, LienEvaluation, ModeleMailSeance, HistoriqueMailSeance
from .forms import SeanceForm, CommunicationSeanceForm
import logging
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.core.mail import EmailMessage
from django.conf import settings

# Vues pour les séances
class SeanceListView(LoginRequiredMixin, ListView):
    model = Seance
    template_name = 'gestion/seance_list.html'
    context_object_name = 'seances'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Seance.objects.prefetch_related('palanques')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__lte=date_fin)
            
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
        palanquees_qs = seance.palanques.select_related('section', 'encadrant').prefetch_related('eleves', 'competences')
        context['palanques'] = palanquees_qs
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs['files'] = self.request.FILES
        return kwargs

class SeanceDeleteView(LoginRequiredMixin, DeleteView):
    model = Seance
    template_name = 'gestion/seance_confirm_delete.html'
    success_url = reverse_lazy('seance_list')

@method_decorator(staff_member_required, name='dispatch')
class CommunicationSeanceView(LoginRequiredMixin, View):
    def get(self, request, pk):
        seance = get_object_or_404(Seance, pk=pk)
        inscrits_qs = seance.inscriptions.order_by('personne__nom')
        inscrits = list(inscrits_qs.values('id', 'personne__nom', 'personne__prenom', 'personne__email'))
        inscrits_choices = [(str(ins['id']), f"{ins['personne__nom']} {ins['personne__prenom']} ({ins['personne__email']})") for ins in inscrits]
        form = CommunicationSeanceForm(inscrits_choices=inscrits_choices)
        return render(request, 'gestion/communication_seance.html', {
            'form': form,
            'seance': seance,
            'inscrits': inscrits,
        })

    def post(self, request, pk):
        seance = get_object_or_404(Seance, pk=pk)
        inscrits_qs = seance.inscriptions.order_by('personne__nom')
        inscrits = list(inscrits_qs.values('id', 'personne__nom', 'personne__prenom', 'personne__email'))
        inscrits_choices = [(str(ins['id']), f"{ins['personne__nom']} {ins['personne__prenom']} ({ins['personne__email']})") for ins in inscrits]
        form = CommunicationSeanceForm(request.POST, request.FILES, inscrits_choices=inscrits_choices)
        if form.is_valid():
            print('[DEBUG] Formulaire valide')
            # Gestion de l'enregistrement du modèle
            if 'enregistrer_modele' in request.POST:
                nom = request.POST.get('nom_modele', '').strip()
                print(f'[DEBUG] Demande d\'enregistrement de modèle, nom saisi : "{nom}"')
                if nom:
                    modele = ModeleMailSeance.objects.create(
                        nom=nom,
                        objet=form.cleaned_data['objet'],
                        contenu=form.cleaned_data['contenu'],
                        auteur=request.user
                    )
                    print(f'[DEBUG] Modèle créé en base avec id={modele.id}')
                    messages.success(request, "Modèle enregistré avec succès.")
                    form = CommunicationSeanceForm(inscrits_choices=inscrits_choices)  # Réinstancie le formulaire pour rafraîchir la liste
                else:
                    print('[DEBUG] Aucun nom de modèle fourni')
                    messages.error(request, "Veuillez donner un nom au modèle.")
                return render(request, 'gestion/communication_seance.html', {
                    'form': form,
                    'seance': seance,
                    'inscrits': inscrits,
                })
            # Gestion de l'envoi du mail
            destinataires = []
            if form.cleaned_data['destinataires'] == 'encadrants':
                destinataires = list(seance.inscriptions.filter(personne__statut='encadrant').values_list('personne__email', flat=True))
            elif form.cleaned_data['destinataires'] == 'eleves':
                destinataires = list(seance.inscriptions.filter(personne__statut='eleve').values_list('personne__email', flat=True))
            elif form.cleaned_data['destinataires'] == 'tous':
                destinataires = list(seance.inscriptions.values_list('personne__email', flat=True))
            elif form.cleaned_data['destinataires'] == 'choix':
                ids = form.cleaned_data['inscrits_choisis']
                destinataires = list(seance.inscriptions.filter(id__in=ids).values_list('personne__email', flat=True))
            destinataires = [email for email in destinataires if email]
            if not destinataires:
                messages.error(request, "Aucun destinataire sélectionné.")
                return render(request, 'gestion/communication_seance.html', {
                    'form': form,
                    'seance': seance,
                    'inscrits': inscrits,
                })
            # Gestion des pièces jointes
            fichiers = request.FILES.getlist('fichiers')
            if len(fichiers) > 5:
                messages.error(request, "Vous ne pouvez joindre que 5 fichiers maximum.")
                return render(request, 'gestion/communication_seance.html', {
                    'form': form,
                    'seance': seance,
                    'inscrits': inscrits,
                })
            for f in fichiers:
                if f.size > 5*1024*1024:
                    messages.error(request, f"Le fichier {f.name} dépasse la taille maximale de 5Mo.")
                    return render(request, 'gestion/communication_seance.html', {
                        'form': form,
                        'seance': seance,
                        'inscrits': inscrits,
                    })
            # Charger les fichiers en mémoire une seule fois pour éviter les problèmes de lecture multiple
            fichiers_data = []
            for f in fichiers:
                f.seek(0)  # S'assurer que le pointeur est au début
                fichiers_data.append({
                    'name': f.name,
                    'content': f.read(),
                    'content_type': f.content_type
                })
            
            # Envoi du mail (BCC)
            email = EmailMessage(
                subject=form.cleaned_data['objet'],
                body=form.cleaned_data['contenu'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                bcc=destinataires,
            )
            email.content_subtype = "html"
            # Utiliser les données pré-chargées au lieu de relire les fichiers
            for f_data in fichiers_data:
                email.attach(f_data['name'], f_data['content'], f_data['content_type'])
            email.send()
            # Historique
            HistoriqueMailSeance.objects.create(
                seance=seance,
                objet=form.cleaned_data['objet'],
                contenu=form.cleaned_data['contenu'],
                destinataires=",".join(destinataires),
                fichiers=",".join([f.name for f in fichiers]),
                auteur=request.user
            )
            messages.success(request, "Mail envoyé avec succès.")
            return redirect('seance_detail', pk=seance.pk)
        else:
            print('[DEBUG] Formulaire NON valide :', form.errors)
            return render(request, 'gestion/communication_seance.html', {
                'form': form,
                'seance': seance,
                'inscrits': inscrits,
            })
