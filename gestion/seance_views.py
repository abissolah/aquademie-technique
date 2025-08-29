from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Seance, Section, LienEvaluation
from .forms import SeanceForm

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
        context['sections'] = Section.objects.all()
        return context

class SeanceDetailView(LoginRequiredMixin, DetailView):
    model = Seance
    template_name = 'gestion/seance_detail.html'
    context_object_name = 'seance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seance = self.get_object()
        
        # Récupérer les palanquées associées
        context['palanquees'] = seance.palanquees.select_related('section', 'encadrant').prefetch_related('eleves', 'competences')
        
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
