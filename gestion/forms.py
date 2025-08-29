from django import forms
from .models import Adherent, Section, Competence, GroupeCompetence, Seance, Palanquee, Evaluation

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
        fields = ['date', 'lieu']
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'lieu': forms.TextInput(attrs={'placeholder': 'Lieu de la séance'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # S'assurer que la date est formatée correctement pour l'affichage HTML
        if self.instance and self.instance.pk:
            if self.instance.date:
                self.fields['date'].initial = self.instance.date.strftime('%Y-%m-%d')

class PalanqueeForm(forms.ModelForm):
    class Meta:
        model = Palanquee
        fields = ['nom', 'seance', 'section', 'encadrant', 'eleves', 'competences', 'precision_exercices']
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': 'Nom de la palanquée'}),
            'precision_exercices': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        # Récupérer la séance depuis les paramètres GET ou l'instance
        seance_id = kwargs.pop('seance_id', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les adhérents selon leur statut
        self.fields['encadrant'].queryset = Adherent.objects.filter(statut='encadrant')
        self.fields['eleves'].queryset = Adherent.objects.filter(statut='eleve')
        
        # Gestion de la séance
        if seance_id:
            # Si une séance est spécifiée, la pré-sélectionner et la rendre en lecture seule
            try:
                seance = Seance.objects.get(pk=seance_id)
                self.fields['seance'].initial = seance
                self.fields['seance'].widget.attrs['readonly'] = True
                self.fields['seance'].widget.attrs['class'] = 'form-control-plaintext'
                self.fields['seance'].help_text = f"Séance sélectionnée : {seance.date} - {seance.lieu}"
            except Seance.DoesNotExist:
                pass
        elif self.instance and self.instance.pk:
            # Pour une modification, rendre la séance en lecture seule
            self.fields['seance'].widget.attrs['readonly'] = True
            self.fields['seance'].widget.attrs['class'] = 'form-control-plaintext'
            self.fields['seance'].help_text = f"Séance : {self.instance.seance.date} - {self.instance.seance.lieu}"
        
        # Filtrer les compétences selon la section sélectionnée
        if 'instance' in kwargs and kwargs['instance']:
            # Pour une modification, utiliser la section de l'instance
            self.fields['competences'].queryset = Competence.objects.filter(section=kwargs['instance'].section)
        else:
            # Pour une création, commencer avec un queryset vide
            self.fields['competences'].queryset = Competence.objects.none()
        
        # Si des données POST sont fournies, mettre à jour le queryset des compétences
        if 'data' in kwargs and kwargs['data']:
            section_id = kwargs['data'].get('section')
            if section_id:
                try:
                    section = Section.objects.get(id=section_id)
                    self.fields['competences'].queryset = Competence.objects.filter(section=section)
                except Section.DoesNotExist:
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
    def __init__(self, palanquee, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.palanquee = palanquee
        
        # Créer un champ pour chaque élève et compétence
        for eleve in palanquee.eleves.all():
            for competence in palanquee.competences.all():
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

 