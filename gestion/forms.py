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
    exercices_prevus = forms.ModelMultipleChoiceField(
        queryset=Exercice.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Exercices à réaliser (groupés par compétence)"
    )

    class Meta:
        model = Palanquee
        fields = ['nom', 'seance', 'section', 'encadrant', 'exercices_prevus', 'precision_exercices', 'duree', 'profondeur_max']
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': 'Nom de la palanquée'}),
            'precision_exercices': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        seance_id = kwargs.pop('seance_id', None)
        super().__init__(*args, **kwargs)
        self.fields['encadrant'].queryset = Adherent.objects.filter(statut='encadrant')
        # Initialiser la séance si passée en paramètre
        if seance_id:
            try:
                seance = Seance.objects.get(pk=seance_id)
                self.fields['seance'].initial = seance
            except Seance.DoesNotExist:
                pass
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
        # Exercices groupés par compétence selon la section
        section = None
        if 'section' in self.data:
            try:
                section = Section.objects.get(pk=self.data['section'])
            except Section.DoesNotExist:
                pass
        elif self.instance and self.instance.pk:
            section = self.instance.section
        if section:
            competences = Competence.objects.filter(section=section).prefetch_related('exercices')
            exercices_ids = set()
            for comp in competences:
                exercices_ids.update(comp.exercices.values_list('id', flat=True))
            self.fields['exercices_prevus'].queryset = Exercice.objects.filter(id__in=exercices_ids)
            # Pour le template : fournir la structure groupée par compétence
            self.competence_exercices = [(comp, comp.exercices.all()) for comp in competences]
        else:
            self.fields['exercices_prevus'].queryset = Exercice.objects.none()
            self.competence_exercices = []

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

class EvaluationExerciceBulkForm(forms.Form):
    def __init__(self, palanquee, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.palanquee = palanquee
        # Pour chaque élève et exercice prévu, créer un champ note (1-3 étoiles) et un champ commentaire
        for eleve in palanquee.eleves.all():
            for exercice in palanquee.exercices_prevus.all():
                field_name = f"eval_{eleve.id}_{exercice.id}"
                self.fields[field_name] = forms.ChoiceField(
                    choices=[(1, '1 étoile'), (2, '2 étoiles'), (3, '3 étoiles')],
                    label=f"{eleve.nom_complet} - {exercice.nom}",
                    required=False,
                    widget=forms.RadioSelect
                )
                comment_field_name = f"comment_{eleve.id}_{exercice.id}"
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
            'telephone', 'photo', 'numero_licence', 'assurance', 'caci_fichier', 'date_delivrance_caci', 'niveau', 'statut'
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
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = True
        self.fields['caci_fichier'].required = True
        self.fields['code_postal'].required = True
        self.fields['ville'].required = True
        self.fields['assurance'].required = False
        self.fields['assurance'].label = 'Assurance personnelle * '
        self.fields['numero_licence'].required = True
        self.fields['numero_licence'].label = 'Numéro de licence (Pour les débutants mettre 0)'
        if 'sections' in self.fields:
            self.fields.pop('sections')

    def clean_date_delivrance_caci(self):
        from datetime import timedelta, date
        date_delivrance = self.cleaned_data.get('date_delivrance_caci')
        if date_delivrance:
            expiration = date_delivrance + timedelta(days=365)
            if expiration < date.today():
                raise forms.ValidationError("Votre CACI doit être valide.")
        return date_delivrance

    def clean_assurance(self):
        # Permettre la valeur vide ('') qui correspond à 'Aucune assurance' même si le champ est requis
        value = self.cleaned_data.get('assurance')
        if value is None:
            return ''
        return value

class ExerciceForm(forms.ModelForm):
    class Meta:
        model = Exercice
        fields = ['nom', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

 