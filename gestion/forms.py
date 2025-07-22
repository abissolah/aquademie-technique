from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Adherent, Section, Competence, GroupeCompetence, Seance, Evaluation

class AdherentForm(forms.ModelForm):
    class Meta:
        model = Adherent
        fields = [
            'nom', 'prenom', 'date_naissance', 'adresse', 'email', 
            'telephone', 'photo', 'date_fin_validite_caci', 'niveau', 'statut', 'sections'
        ]
        widgets = {
            'date_naissance': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'date_fin_validite_caci': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'adresse': forms.Textarea(attrs={'rows': 3}),
            'sections': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # S'assurer que les dates sont formatées correctement pour l'affichage HTML
        if self.instance and self.instance.pk:
            if self.instance.date_naissance:
                self.fields['date_naissance'].initial = self.instance.date_naissance.strftime('%Y-%m-%d')
            if self.instance.date_fin_validite_caci:
                self.fields['date_fin_validite_caci'].initial = self.instance.date_fin_validite_caci.strftime('%Y-%m-%d')

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['nom', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class CompetenceForm(forms.ModelForm):
    class Meta:
        model = Competence
        fields = ['nom', 'description', 'section']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class GroupeCompetenceForm(forms.ModelForm):
    class Meta:
        model = GroupeCompetence
        fields = ['section', 'intitule', 'competences', 'competences_attendues', 'technique', 'modalites_evaluation']
        widgets = {
            'competences_attendues': forms.Textarea(attrs={'rows': 3}),
            'technique': forms.Textarea(attrs={'rows': 3}),
            'modalites_evaluation': forms.Textarea(attrs={'rows': 3}),
        }

class SeanceForm(forms.ModelForm):
    class Meta:
        model = Seance
        fields = ['palanquee', 'date', 'section', 'encadrant', 'eleves', 'competences', 'precision_exercices']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'precision_exercices': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les adhérents selon leur statut
        self.fields['encadrant'].queryset = Adherent.objects.filter(statut='encadrant')
        self.fields['eleves'].queryset = Adherent.objects.filter(statut='eleve')
        
        # Filtrer les compétences selon la section sélectionnée
        if 'instance' in kwargs and kwargs['instance']:
            self.fields['competences'].queryset = Competence.objects.filter(section=kwargs['instance'].section)
        else:
            self.fields['competences'].queryset = Competence.objects.none()

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['note', 'commentaire']
        widgets = {
            'note': forms.Select(choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(6)]),
            'commentaire': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Commentaire optionnel...'}),
        }

class EvaluationBulkForm(forms.Form):
    def __init__(self, seance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seance = seance
        
        # Créer un champ pour chaque élève et compétence
        for eleve in seance.eleves.all():
            for competence in seance.competences.all():
                field_name = f"eval_{eleve.id}_{competence.id}"
                self.fields[field_name] = forms.ChoiceField(
                    choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(6)],
                    label=f"{eleve.nom_complet} - {competence.nom}",
                    required=False,
                    initial=0
                )
                
                # Champ commentaire optionnel
                comment_field_name = f"comment_{eleve.id}_{competence.id}"
                self.fields[comment_field_name] = forms.CharField(
                    widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Commentaire...'}),
                    required=False,
                    label=""
                )

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2') 