from django import forms
from .models import Adherent, Section, Competence, GroupeCompetence, Seance, Palanquee, Evaluation, Lieu, Exercice, ModeleMailSeance, ModeleMailAdherents
from ckeditor_uploader.widgets import CKEditorUploadingWidget

DESTINATAIRES_CHOICES = [
    ("encadrants", "Les encadrants de la séance"),
    ("eleves", "Les élèves de la séance"),
    ("tous", "Tous les inscrits à la séance"),
    ("choix", "Choisir parmi les inscrits"),
]

class CommunicationSeanceForm(forms.Form):
    destinataires = forms.ChoiceField(
        choices=DESTINATAIRES_CHOICES,
        label="Destinataires",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    inscrits_choisis = forms.MultipleChoiceField(
        required=False,
        label="Inscrits à sélectionner",
        widget=forms.CheckboxSelectMultiple,
        choices=[]  # sera défini dynamiquement
    )
    objet = forms.CharField(
        max_length=255,
        label="Objet du mail",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    contenu = forms.CharField(
        label="Contenu du mail",
        widget=CKEditorUploadingWidget()
    )
    fichiers = forms.FileField(
        label="Pièces jointes",
        required=False,
        widget=forms.FileInput(),
        help_text="Jusqu'à 5 fichiers, 5Mo max chacun."
    )
    modele = forms.ModelChoiceField(
        queryset=ModeleMailSeance.objects.all(),
        required=False,
        label="Charger un modèle",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, inscrits_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if inscrits_choices is not None:
            self.fields['inscrits_choisis'].choices = inscrits_choices

class AdherentForm(forms.ModelForm):
    caci_valide = forms.BooleanField(label="CACI validé", required=False)
    actif = forms.BooleanField(label="Actif", required=False)
    class Meta:
        model = Adherent
        fields = [
            'nom', 'prenom', 'date_naissance', 'adresse', 'code_postal', 'ville', 'email', 
            'telephone', 'photo', 'numero_licence', 'assurance', 'date_delivrance_caci', 'niveau', 'statut', 'sections',
            'type_personne', 'caci_fichier', 'caci_valide', 'actif'
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['exercices'].queryset = Exercice.objects.filter(type=Exercice.TYPE_CLASSIQUE)
        self.fields['exercices_evaluation'] = forms.ModelMultipleChoiceField(
            queryset=Exercice.objects.filter(type=Exercice.TYPE_EVALUATION),
            required=False,
            widget=forms.SelectMultiple(),
            label="Exercices d'évaluation",
        )
        if self.instance and self.instance.pk:
            self.fields['exercices'].initial = self.instance.exercices.filter(type=Exercice.TYPE_CLASSIQUE)
            self.fields['exercices_evaluation'].initial = self.instance.exercices.filter(type=Exercice.TYPE_EVALUATION)

    def save(self, commit=True):
        competence = super().save(commit=commit)
        exercices_classiques = self.cleaned_data.get('exercices', Exercice.objects.none())
        exercices_evaluation = self.cleaned_data.get('exercices_evaluation', Exercice.objects.none())

        def _save_m2m():
            competence.exercices.set(list(exercices_classiques) + list(exercices_evaluation))

        if commit:
            _save_m2m()
        else:
            self._save_m2m = _save_m2m
        return competence

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
    presence_president = forms.BooleanField(label="Présence du président", required=False)
    class Meta:
        model = Seance
        fields = [
            'date',
            'heure_debut',
            'heure_fin',
            'lieu',
            'directeur_plongee',
            'presence_president',
            'fiche_securite_previsionnelle',
            'fiche_securite_validee'
        ]
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
        self.seance_type = kwargs.pop('seance_type', Seance.TYPE_SEANCE)
        super().__init__(*args, **kwargs)
        # S'assurer que la date est formatée correctement pour l'affichage HTML
        if self.instance and self.instance.pk:
            if self.instance.date:
                self.fields['date'].initial = self.instance.date.strftime('%Y-%m-%d')
        # Utiliser une liste déroulante pour le lieu
        self.fields['lieu'].queryset = Lieu.objects.all()
        self.fields['lieu'].label_from_instance = lambda obj: f"{obj.nom} - {obj.ville}"
        # Encadrants adhérents et non adhérents
        self.fields['directeur_plongee'].queryset = Adherent.objects.filter(
            statut='encadrant'
        ).order_by('nom', 'prenom')
        self.fields['lieu'].required = self.seance_type == Seance.TYPE_SEANCE

        def _label_directeur_plongee(obj):
            base = f"{obj.nom_complet} ({obj.get_niveau_display()})"
            if obj.type_personne == 'non_adherent':
                return f"{base} — {obj.get_type_personne_display()}"
            return base

        self.fields['directeur_plongee'].label_from_instance = _label_directeur_plongee

    def clean(self):
        cleaned_data = super().clean()
        if self.seance_type == Seance.TYPE_SEANCE and not cleaned_data.get('lieu'):
            self.add_error('lieu', "Le lieu est obligatoire pour une séance.")
        return cleaned_data

def _resoudre_seance_palanquee_form(seance_id=None, instance=None, data=None):
    if seance_id:
        try:
            return Seance.objects.get(pk=seance_id)
        except Seance.DoesNotExist:
            return None
    if instance and instance.pk:
        return instance.seance
    if data and 'seance' in data:
        try:
            return Seance.objects.get(pk=data['seance'])
        except Seance.DoesNotExist:
            return None
    return None


def exercices_disponibles_pour_palanquee(seance, section=None):
    if seance and seance.est_sortie:
        return Exercice.objects.filter(type=Exercice.TYPE_EVALUATION).order_by('nom')
    if section:
        competences = Competence.objects.filter(section=section).prefetch_related('exercices')
        exercices_ids = set()
        for comp in competences:
            exercices_ids.update(
                comp.exercices.filter(type=Exercice.TYPE_CLASSIQUE).values_list('id', flat=True)
            )
        return Exercice.objects.filter(id__in=exercices_ids).order_by('nom')
    return Exercice.objects.none()


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
        self.fields['encadrant'].required = False
        self.fields['precision_exercices'].label = 'Nota'
        self.fields['precision_exercices'].required = False
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
        seance = _resoudre_seance_palanquee_form(
            seance_id=seance_id,
            instance=self.instance,
            data=self.data if hasattr(self, 'data') else None,
        )
        self.is_sortie = bool(seance and seance.est_sortie)

        section = None
        if 'section' in self.data:
            try:
                section = Section.objects.get(pk=self.data['section'])
            except Section.DoesNotExist:
                pass
        elif self.instance and self.instance.pk:
            section = self.instance.section

        self.fields['exercices_prevus'].queryset = exercices_disponibles_pour_palanquee(seance, section)
        if self.is_sortie:
            self.competence_exercices = []
        elif section:
            competences = Competence.objects.filter(section=section).prefetch_related('exercices')
            self.competence_exercices = [
                (comp, comp.exercices.filter(type=Exercice.TYPE_CLASSIQUE).order_by('nom'))
                for comp in competences
            ]
        else:
            self.competence_exercices = []

        self.exercices_prevus_selectionnes = set()
        if self.instance.pk:
            self.exercices_prevus_selectionnes = set(
                self.instance.exercices_prevus_pour_seance().values_list('id', flat=True)
            )

    def clean_exercices_prevus(self):
        exercices = self.cleaned_data.get('exercices_prevus')
        if not exercices:
            return exercices
        seance = _resoudre_seance_palanquee_form(
            instance=self.instance,
            data=self.data,
        )
        if not seance:
            return exercices
        type_attendu = Exercice.TYPE_EVALUATION if seance.est_sortie else Exercice.TYPE_CLASSIQUE
        return exercices.filter(type=type_attendu)

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
            for exercice in palanquee.exercices_prevus_pour_seance():
                field_name = f"eval_{eleve.id}_{exercice.id}"
                self.fields[field_name] = forms.ChoiceField(
                    choices=[(1, '1 étoile'), (2, '2 étoiles'), (3, '3 étoiles')],
                    label=f"{eleve.nom_complet} - {exercice.nom}",
                    required=False,
                    widget=forms.RadioSelect
                )
                # Champ raison de non réalisation
                raison_field_name = f"raison_{eleve.id}_{exercice.id}"
                from .models import EvaluationExercice
                self.fields[raison_field_name] = forms.ChoiceField(
                    choices=[('', '-- Sélectionner une raison --')] + EvaluationExercice.RAISON_NON_REALISE_CHOICES,
                    label="",
                    required=False,
                    widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
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
        self.fields['date_delivrance_caci'].required = True
        self.fields['code_postal'].required = True
        self.fields['ville'].required = True
        self.fields['assurance'].required = False
        self.fields['assurance'].label = 'Assurance personnelle * '
        self.fields['numero_licence'].required = True
        self.fields['numero_licence'].label = 'Numéro de licence (Pour les débutants mettre 0)'
        if 'sections' in self.fields:
            self.fields.pop('sections')

    #def clean_date_delivrance_caci(self):
    #    from datetime import timedelta, date
    #    date_delivrance = self.cleaned_data.get('date_delivrance_caci')
    #    if date_delivrance:
    #        expiration = date_delivrance + timedelta(days=365)
    #        if expiration < date.today():
    #            raise forms.ValidationError("Votre CACI doit être valide.")
    #    return date_delivrance

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


class ExerciceEvaluationForm(forms.ModelForm):
    class Meta:
        model = Exercice
        fields = ['nom', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class SelectWithSeparator(forms.Select):
    """Select widget qui affiche l'option de valeur __sep__ comme un trait désactivé."""
    SEPARATOR_VALUE = '__sep__'

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value == self.SEPARATOR_VALUE:
            option['attrs']['disabled'] = True
        return option


class AdminInscriptionSeanceForm(forms.Form):
    adherent = forms.ChoiceField(
        choices=[],  # rempli dans __init__
        required=False,
        label="Adhérent / Non adhérent",
        help_text="Sélectionner un adhérent ou un non adhérent existant, OU remplir les champs ci-dessous pour un nouveau non adhérent.",
        widget=SelectWithSeparator(attrs={'class': 'form-select'})
    )
    # Champs pour non adhérent
    nom = forms.CharField(required=False, label="Nom")
    prenom = forms.CharField(required=False, label="Prénom")
    date_naissance = forms.DateField(required=False, label="Date de naissance", widget=forms.DateInput(attrs={'type': 'date'}))
    adresse = forms.CharField(required=False, label="Adresse")
    code_postal = forms.CharField(required=False, label="Code postal")
    ville = forms.CharField(required=False, label="Ville")
    email = forms.EmailField(required=False, label="Email")
    telephone = forms.CharField(required=False, label="Téléphone")
    numero_licence = forms.CharField(required=False, label="Numéro de licence")
    assurance = forms.ChoiceField(
        choices=[
            ('', 'Aucune assurance'),
            ('Piscine', 'Piscine'),
            ('Loisir 1', 'Loisir 1'),
            ('Loisir 2', 'Loisir 2'),
            ('Loisir 3', 'Loisir 3'),
            ('Loisir Top 1', 'Loisir Top 1'),
            ('Loisir Top 2', 'Loisir Top 2'),
            ('Loisir Top 3', 'Loisir Top 3'),
        ],
        required=False,
        label="Assurance"
    )
    caci_fichier = forms.FileField(required=False, label="Fichier CACI")
    date_delivrance_caci = forms.DateField(required=False, label="Date de délivrance du CACI", widget=forms.DateInput(attrs={'type': 'date'}))
    niveau = forms.ChoiceField(
        choices=[
            ('', 'Niveau'),
            ('debutant', 'Débutant'),
            ('niveau1', 'Niveau 1'),
            ('niveau2', 'Niveau 2'),
            ('niveau3', 'Niveau 3'),
            ('initiateur1', 'Initiateur 1'),
            ('initiateur2', 'Initiateur 2'),
            ('moniteur_federal1', 'Moniteur fédéral 1'),
            ('moniteur_federal2', 'Moniteur fédéral 2'),
        ],
        required=False,
        label="Niveau"
    )
    statut = forms.ChoiceField(
        choices=[('eleve', 'Élève'), ('encadrant', 'Encadrant')],
        required=False,
        label="Statut"
    )
    sections = forms.ModelMultipleChoiceField(
        queryset=Section.objects.all().order_by('nom'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Sections",
    )
    covoiturage = forms.ChoiceField(
        choices=[('', '---'), ('none', 'Je ne souhaite pas de covoiturage'), ('propose', 'Je peux proposer du covoiturage'), ('besoin', "J'aurai besoin de covoiturage")],
        required=False,
        label="Covoiturage"
    )
    lieu_covoiturage = forms.CharField(
        max_length=255,
        required=False,
        label="Lieu de prise en charge"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        adherents = Adherent.objects.filter(type_personne='adherent', actif=True).order_by('nom', 'prenom')
        non_adherents = Adherent.objects.filter(type_personne='non_adherent', actif=True).order_by('nom', 'prenom')
        choices = [('', '---------')]
        choices += [(str(a.pk), str(a)) for a in adherents]
        choices += [(SelectWithSeparator.SEPARATOR_VALUE, '──────────')]
        choices += [(str(a.pk), str(a)) for a in non_adherents]
        self.fields['adherent'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        raw_adherent = cleaned_data.get('adherent')
        if raw_adherent and raw_adherent != SelectWithSeparator.SEPARATOR_VALUE:
            try:
                cleaned_data['adherent'] = Adherent.objects.get(pk=int(raw_adherent))
            except (ValueError, Adherent.DoesNotExist):
                cleaned_data['adherent'] = None
        else:
            cleaned_data['adherent'] = None
        adherent = cleaned_data.get('adherent')
        nom = cleaned_data.get('nom')
        prenom = cleaned_data.get('prenom')
        email = cleaned_data.get('email')
        if not adherent and not (nom and prenom and email):
            raise forms.ValidationError("Sélectionnez un adhérent ou un non adhérent OU renseignez nom, prénom et email pour un nouveau non adhérent.")
        return cleaned_data

class PublicNonAdherentInscriptionForm(forms.ModelForm):
    covoiturage = forms.ChoiceField(
        choices=[('', '--'), ('none', 'Je ne souhaite pas de covoiturage'), ('propose', 'Je peux proposer du covoiturage'), ('besoin', 'J\'aurai besoin de covoiturage')],
        required=False,
        label="Covoiturage"
    )
    lieu_covoiturage = forms.CharField(
        required=False,
        label="Lieu de prise en charge du covoiturage"
    )
    type_non_adherent = forms.ChoiceField(
        choices=[('bapteme', 'Je suis débutant (baptême)'), ('plongeur', 'Je suis plongeur / encadrant')],
        widget=forms.RadioSelect,
        required=True,
        label="Type d'inscription"
    )

    class Meta:
        model = Adherent
        fields = [
            'type_non_adherent', 'nom', 'prenom', 'date_naissance', 'adresse', 'code_postal', 'ville', 'email',
            'telephone', 'photo', 'numero_licence', 'assurance', 'caci_fichier', 'date_delivrance_caci',
            'niveau', 'statut'
        ]
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'date_delivrance_caci': forms.DateInput(attrs={'type': 'date'}),
            'adresse': forms.TextInput(),
            'niveau': forms.Select(choices=[
                ('', 'Niveau'),
                ('debutant', 'Débutant'),
                ('niveau1', 'Niveau 1'),
                ('niveau2', 'Niveau 2'),
                ('niveau3', 'Niveau 3'),
                ('initiateur1', 'Initiateur 1'),
                ('initiateur2', 'Initiateur 2'),
                ('moniteur_federal1', 'Moniteur fédéral 1'),
                ('moniteur_federal2', 'Moniteur fédéral 2'),
            ]),
            'statut': forms.Select(choices=[('eleve', 'Élève'), ('encadrant', 'Encadrant')]),
            'assurance': forms.Select(choices=[
                ('', 'Aucune assurance'),
                ('Piscine', 'Piscine'),
                ('Loisir 1', 'Loisir 1'),
                ('Loisir 2', 'Loisir 2'),
                ('Loisir 3', 'Loisir 3'),
                ('Loisir Top 1', 'Loisir Top 1'),
                ('Loisir Top 2', 'Loisir Top 2'),
                ('Loisir Top 3', 'Loisir Top 3'),
            ]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Par défaut, certains champs ne sont requis que pour plongeur/encadrant
        self.fields['caci_fichier'].required = False
        self.fields['date_delivrance_caci'].required = False
        self.fields['photo'].required = False
        self.fields['numero_licence'].required = False
        self.fields['assurance'].required = False
        self.fields['niveau'].required = True
        self.fields['statut'].required = True
        # Suppression du champ sections
        if 'sections' in self.fields:
            self.fields.pop('sections')

    def clean(self):
        cleaned_data = super().clean()
        type_non_adherent = cleaned_data.get('type_non_adherent')
        # Pour plongeur/encadrant, CACI obligatoire
        if type_non_adherent == 'plongeur':
            if not cleaned_data.get('caci_fichier'):
                self.add_error('caci_fichier', 'Le fichier CACI est obligatoire pour les plongeurs/encadrants.')
            if not cleaned_data.get('date_delivrance_caci'):
                self.add_error('date_delivrance_caci', 'La date de délivrance du CACI est obligatoire pour les plongeurs/encadrants.')
        return cleaned_data

    def clean_date_delivrance_caci(self):
        from datetime import timedelta, date
        date_delivrance = self.cleaned_data.get('date_delivrance_caci')
        if date_delivrance:
            expiration = date_delivrance + timedelta(days=365)
            if expiration < date.today():
                raise forms.ValidationError("Votre CACI doit être valide.")
        return date_delivrance

class AffectationSectionMasseForm(forms.Form):
    section = forms.ModelChoiceField(queryset=Section.objects.all(), label="Section à affecter", required=True)
    adherents = forms.ModelMultipleChoiceField(
        queryset=Adherent.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Adhérents sans section",
        required=True
    )
    def __init__(self, *args, **kwargs):
        adherents_queryset = kwargs.pop('adherents_queryset', None)
        super().__init__(*args, **kwargs)
        if adherents_queryset is not None:
            # Ordonner par nom, prénom
            adherents_queryset = adherents_queryset.order_by('nom', 'prenom')
            self.fields['adherents'].queryset = adherents_queryset
            # Afficher Nom Prénom comme label
            self.fields['adherents'].label_from_instance = lambda obj: f"{obj.nom.upper()} {obj.prenom.capitalize()} ({obj.email})"

ADHERENTS_DESTINATAIRES_CHOICES = [
    ("aucun", "Aucun destinataire"),
    ("tous", "tout le monde"),
    ("personne_adherent", "Tous les adhérents"),
    ("statut_encadrant", "Tous les encadrants"),
    ("statut_eleve", "Tous les élèves"),
    ("membres_du_codir", "Membres du codir"),
    ("section_prepa_niveau1", "Les élèves de la section PN1 (prépa niveau 1)"),
    ("section_prepa_niveau2", "Les élèves de la section PN2 (prépa niveau 2)"),
    ("section_prepa_niveau3", "Les élèves de la section PN3 (prépa niveau 3)"),
    ("section_niveau3", "Les élèves de la section niveau 3"),
    ("section_encadrants", "Les élèves de la section encadrants"),
    
    
]

class CommunicationAdherentsForm(forms.Form):
    destinataires = forms.ChoiceField(
        choices=[],  # Sera rempli dynamiquement avec les listes personnalisées
        label="Destinataires",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    inscrits_choisis = forms.MultipleChoiceField(
        required=False,
        label="Adhérents à sélectionner",
        widget=forms.CheckboxSelectMultiple,
        choices=[]  # sera défini dynamiquement
    )
    objet = forms.CharField(
        max_length=255,
        label="Objet du mail",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    contenu = forms.CharField(
        label="Contenu du mail",
        widget=CKEditorUploadingWidget()
    )
    fichiers = forms.FileField(
        label="Pièces jointes",
        required=False,
        widget=forms.FileInput(),
        help_text="Jusqu'à 5 fichiers, 5Mo max chacun."
    )
    modele = forms.ModelChoiceField(
        queryset=ModeleMailAdherents.objects.all(),
        required=False,
        label="Charger un modèle",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, inscrits_choices=None, listes_diffusion=None, **kwargs):
        super().__init__(*args, **kwargs)
        if inscrits_choices is not None:
            self.fields['inscrits_choisis'].choices = inscrits_choices
        
        # Construire les choix de destinataires avec les listes personnalisées
        choices = list(ADHERENTS_DESTINATAIRES_CHOICES)
        if listes_diffusion is not None:
            # Ajouter les listes personnalisées avec un préfixe pour les identifier
            for liste in listes_diffusion:
                choices.append((f"liste_{liste.id}", f"📋 {liste.nom} ({liste.adherents.count()} adhérent(s))"))
        self.fields['destinataires'].choices = choices

 