from django import forms
from .models import Adherent, Section, Competence, GroupeCompetence, Seance, Palanquee, Evaluation, Lieu, Exercice

class AdherentForm(forms.ModelForm):
    class Meta:
        model = Adherent
        fields = [
            'nom', 'prenom', 'date_naissance', 'adresse', 'code_postal', 'ville', 'email', 
            'telephone', 'photo', 'numero_licence', 'assurance', 'date_delivrance_caci', 'niveau', 'statut', 'sections',
            'type_personne', 'caci_fichier'
        ]
        widgets = {
            'date_naissance': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'date_delivrance_caci': forms.DateInput(
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
            if self.instance.date_delivrance_caci:
                self.fields['date_delivrance_caci'].initial = self.instance.date_delivrance_caci.strftime('%Y-%m-%d')
        if 'nom' in self.fields and self.instance and self.instance.nom:
            self.fields['nom'].initial = self.instance.nom.upper()
        if 'prenom' in self.fields and self.instance and self.instance.prenom:
            self.fields['prenom'].initial = self.instance.prenom.capitalize()

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
        fields = ['nom', 'description', 'exercices', 'section']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'exercices': forms.SelectMultiple(),
        }

class GroupeCompetenceForm(forms.ModelForm):
    class Meta:
        model = GroupeCompetence
        fields = ['section', 'intitule', 'competences', 'competences_attendues', 'technique', 'comportements', 'theorie', 'modalites_evaluation']
        widgets = {
            'competences_attendues': forms.Textarea(attrs={'rows': 3}),
            'technique': forms.Textarea(attrs={'rows': 3}),
            'comportements': forms.Textarea(attrs={'rows': 3}),
            'theorie': forms.Textarea(attrs={'rows': 3}),
            'modalites_evaluation': forms.Textarea(attrs={'rows': 3}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comportements'].required = True
        self.fields['theorie'].required = True

class SeanceForm(forms.ModelForm):
    class Meta:
        model = Seance
        fields = ['date', 'heure_debut', 'heure_fin', 'lieu', 'directeur_plongee']
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'heure_debut': forms.TimeInput(
                attrs={'type': 'time', 'step': 900},  # 900s = 15min
                format='%H:%M'
            ),
            'heure_fin': forms.TimeInput(
                attrs={'type': 'time', 'step': 900},
                format='%H:%M'
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # S'assurer que la date est formatée correctement pour l'affichage HTML
        if self.instance and self.instance.pk:
            if self.instance.date:
                self.fields['date'].initial = self.instance.date.strftime('%Y-%m-%d')
        # Utiliser une liste déroulante pour le lieu
        self.fields['lieu'].queryset = Lieu.objects.all()
        self.fields['lieu'].label_from_instance = lambda obj: f"{obj.nom} - {obj.ville}"
        # Filtrer les encadrants adhérents pour directeur de plongée
        self.fields['directeur_plongee'].queryset = Adherent.objects.filter(statut='encadrant', type_personne='adherent')
        self.fields['directeur_plongee'].label_from_instance = lambda obj: f"{obj.nom_complet} ({obj.get_niveau_display()})"

class PalanqueeForm(forms.ModelForm):
    class Meta:
        model = Palanquee
        fields = ['nom', 'seance', 'section', 'encadrant', 'eleves', 'competences', 'precision_exercices', 'duree', 'profondeur_max']
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

        # Pré-remplir le nom pour une création
        if not self.instance.pk:
            seance = None
            if seance_id:
                try:
                    seance = Seance.objects.get(pk=seance_id)
                except Seance.DoesNotExist:
                    pass
            elif 'seance' in self.data:
                try:
                    seance = Seance.objects.get(pk=self.data['seance'])
                except Seance.DoesNotExist:
                    pass
            if seance:
                count = seance.palanques.count()
                self.fields['nom'].initial = f"P{count+1}"

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

class NonAdherentInscriptionForm(forms.ModelForm):
    class Meta:
        model = Adherent
        fields = [
            'nom', 'prenom', 'date_naissance', 'adresse', 'code_postal', 'ville', 'email',
            'telephone', 'photo', 'numero_licence', 'assurance', 'date_delivrance_caci', 'niveau', 'statut', 'sections', 'caci_fichier'
        ]
        widgets = {
            'date_naissance': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'date_delivrance_caci': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'adresse': forms.Textarea(attrs={'rows': 3}),
            'sections': forms.CheckboxSelectMultiple(),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['caci_fichier'].required = True

class AdherentPublicForm(forms.ModelForm):
    class Meta:
        model = Adherent
        fields = [
            'nom', 'prenom', 'date_naissance', 'adresse', 'code_postal', 'ville', 'email',
            'telephone', 'numero_licence', 'assurance', 'caci_fichier', 'date_delivrance_caci', 'niveau', 'statut'
        ]
        widgets = {
            'date_naissance': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'date_delivrance_caci': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['caci_fichier'].required = True
        self.fields['assurance'].label = "Assurance personnelle"
        if self.instance and self.instance.pk:
            if self.instance.date_naissance:
                self.fields['date_naissance'].initial = self.instance.date_naissance.strftime('%Y-%m-%d')
            if self.instance.date_delivrance_caci:
                self.fields['date_delivrance_caci'].initial = self.instance.date_delivrance_caci.strftime('%Y-%m-%d')
        if 'nom' in self.fields and self.instance and self.instance.nom:
            self.fields['nom'].initial = self.instance.nom.upper()
        if 'prenom' in self.fields and self.instance and self.instance.prenom:
            self.fields['prenom'].initial = self.instance.prenom.capitalize()
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.type_personne = 'adherent'
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class ExerciceForm(forms.ModelForm):
    class Meta:
        model = Exercice
        fields = ['nom', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

 