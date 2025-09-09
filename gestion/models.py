from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class Section(models.Model):
    SECTIONS_CHOICES = [
        ('bapteme', 'Baptême'),
        ('prepa_niveau1', 'Prépa Niveau 1'),
        ('prepa_niveau2', 'Prépa Niveau 2'),
        ('prepa_niveau3', 'Prépa Niveau 3'),
        ('prepa_niveau4', 'Prépa Niveau 4'),
        ('niveau3', 'Niveau 3'),
        ('niveau4', 'Niveau 4'),
        ('encadrant', 'Encadrant'),
    ]
    
    nom = models.CharField(max_length=20, choices=SECTIONS_CHOICES, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"
    
    def __str__(self):
        return self.get_nom_display()

class Adherent(models.Model):
    NIVEAUX_CHOICES = [
        ('debutant', 'Débutant'),
        ('niveau1', 'Niveau 1'),
        ('niveau2', 'Niveau 2'),
        ('niveau3', 'Niveau 3'),
        ('initiateur1', 'Initiateur 1'),
        ('initiateur2', 'Initiateur 2'),
        ('moniteur_federal1', 'Moniteur fédéral 1'),
        ('moniteur_federal2', 'Moniteur fédéral 2'),
    ]
    
    STATUT_CHOICES = [
        ('eleve', 'Élève'),
        ('encadrant', 'Encadrant'),
    ]
    
    TYPE_PERSONNE_CHOICES = [
        ('adherent', 'Adhérent du club'),
        ('non_adherent', 'Non adhérent (invité, renfort, autre club)'),
    ]
    type_personne = models.CharField(max_length=20, choices=TYPE_PERSONNE_CHOICES, default='adherent', verbose_name="Type de personne")
    caci_fichier = models.FileField(upload_to='caci/', blank=True, null=True, verbose_name="Fichier CACI")
    caci_valide = models.BooleanField("CACI validé", default=False)
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    adresse = models.TextField()
    code_postal = models.CharField(max_length=10, blank=True, verbose_name="Code postal")
    ville = models.CharField(max_length=100, blank=True, verbose_name="Ville")
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    photo = models.ImageField(upload_to='photos_adherents/', blank=True, null=True)
    numero_licence = models.CharField(max_length=50, blank=True, null=True, verbose_name="Numéro de licence")
    ASSURANCE_CHOICES = [
        ('', 'Aucune assurance'),
        ('Piscine', 'Piscine'),
        ('Loisir 1', 'Loisir 1'),
        ('Loisir 2', 'Loisir 2'),
        ('Loisir 3', 'Loisir 3'),
        ('Loisir Top 1', 'Loisir Top 1'),
        ('Loisir Top 2', 'Loisir Top 2'),
        ('Loisir Top 3', 'Loisir Top 3'),
    ]
    assurance = models.CharField(max_length=20, choices=ASSURANCE_CHOICES, blank=True, default='', verbose_name="Assurance")
    date_delivrance_caci = models.DateField(verbose_name="Date de délivrance du CACI", null=True, blank=True)
    niveau = models.CharField(max_length=20, choices=NIVEAUX_CHOICES)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='eleve')
    sections = models.ManyToManyField(Section, related_name='adherents', blank=True, verbose_name="Sections")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Adhérent"
        verbose_name_plural = "Adhérents"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    def save(self, *args, **kwargs):
        if self.nom:
            self.nom = self.nom.upper()
        if self.prenom:
            self.prenom = self.prenom.capitalize()
        super().save(*args, **kwargs)

class Exercice(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Exercice"
        verbose_name_plural = "Exercices"
        ordering = ['nom']

    def __str__(self):
        return self.nom

class Competence(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='competences')
    exercices = models.ManyToManyField('Exercice', related_name='competences', blank=True, verbose_name="Exercices")
    
    class Meta:
        verbose_name = "Compétence"
        verbose_name_plural = "Compétences"
        ordering = ['section', 'nom']
    
    def __str__(self):
        return f"{self.section.get_nom_display()} - {self.nom}"

class GroupeCompetence(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='groupes_competences')
    intitule = models.CharField(max_length=200)
    competences = models.ManyToManyField(Competence, related_name='groupes')
    competences_attendues = models.TextField()
    technique = models.TextField()
    modalites_evaluation = models.TextField()
    comportements = models.TextField(blank=True)
    theorie = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Groupe de compétences"
        verbose_name_plural = "Groupes de compétences"
        ordering = ['section', 'intitule']
    
    def __str__(self):
        return f"{self.section.get_nom_display()} - {self.intitule}"

class Lieu(models.Model):
    nom = models.CharField(max_length=200)
    adresse = models.CharField(max_length=255)
    code_postal = models.CharField(max_length=10)
    ville = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Lieu"
        verbose_name_plural = "Lieux"
        ordering = ['nom', 'ville']

    def __str__(self):
        return f"{self.nom} - {self.ville}"

class Seance(models.Model):
    date = models.DateField()
    heure_debut = models.TimeField(verbose_name="Heure de début", null=True, blank=True)
    heure_fin = models.TimeField(verbose_name="Heure de fin", null=True, blank=True)
    lieu = models.ForeignKey(Lieu, on_delete=models.PROTECT, related_name='seances')
    directeur_plongee = models.ForeignKey(
        Adherent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seances_dirigees',
        limit_choices_to={'statut': 'encadrant', 'type_personne': 'adherent'},
        verbose_name="Directeur de plongée"
    )
    presence_president = models.BooleanField("Présence du président", default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Séance"
        verbose_name_plural = "Séances"
        ordering = ['-date', 'lieu']
    
    def __str__(self):
        return f"{self.date} - {self.lieu}"
    
    @property
    def palanques_count(self):
        return self.palanques.count()

class Palanquee(models.Model):
    nom = models.CharField(max_length=200)
    seance = models.ForeignKey(Seance, on_delete=models.CASCADE, related_name='palanques')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='palanques')
    encadrant = models.ForeignKey(Adherent, on_delete=models.SET_NULL, null=True, blank=True, related_name='palanques_encadrees', limit_choices_to={'statut': 'encadrant'})
    competences = models.ManyToManyField(Competence, related_name='palanques')
    precision_exercices = models.TextField()
    duree = models.IntegerField("Durée (minutes)", null=True, blank=True)
    profondeur_max = models.IntegerField("Profondeur max (mètres)", null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    eleves = models.ManyToManyField(Adherent, through='PalanqueeEleve', related_name='palanques_suivies', limit_choices_to={'statut': 'eleve'})
    exercices_prevus = models.ManyToManyField('Exercice', related_name='palanquees_prevues', blank=True, verbose_name="Exercices prévus")
    
    class Meta:
        verbose_name = "Palanquée"
        verbose_name_plural = "Palanquées"
        ordering = ['seance__date', 'nom']
    
    def __str__(self):
        return f"{self.seance.date} - {self.nom} - {self.encadrant.nom_complet}"

class Evaluation(models.Model):
    palanquee = models.ForeignKey(Palanquee, on_delete=models.CASCADE, related_name='evaluations')
    eleve = models.ForeignKey(Adherent, on_delete=models.CASCADE, related_name='evaluations_recues', limit_choices_to={'statut': 'eleve'})
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='evaluations')
    note = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], help_text="0 = pas maîtrisé, 5 = parfaitement maîtrisé")
    commentaire = models.TextField(blank=True)
    date_evaluation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        unique_together = ['palanquee', 'eleve', 'competence']
    
    def __str__(self):
        return f"{self.palanquee} - {self.eleve.nom_complet} - {self.competence.nom} ({self.note}/5)"

class LienEvaluation(models.Model):
    palanquee = models.ForeignKey(Palanquee, on_delete=models.CASCADE, related_name='liens_evaluation')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
    est_valide = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Lien d'évaluation"
        verbose_name_plural = "Liens d'évaluation"
    
    def __str__(self):
        return f"Lien évaluation {self.palanquee} - {self.token}"
    
    @property
    def url_evaluation(self):
        return f"/evaluation/{self.token}/"

class LienInscriptionSeance(models.Model):
    seance = models.ForeignKey('Seance', on_delete=models.CASCADE, related_name='liens_inscription')
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    date_expiration = models.DateTimeField()

    def __str__(self):
        return f"Lien pour {self.seance} (expire le {self.date_expiration})"

class InscriptionSeance(models.Model):
    COVOITURAGE_CHOICES = [
        ("none", "Je ne souhaite pas de covoiturage"),
        ("propose", "Je peux proposer du covoiturage"),
        ("besoin", "J'aurai besoin de covoiturage"),
    ]
    seance = models.ForeignKey('Seance', on_delete=models.CASCADE, related_name='inscriptions')
    personne = models.ForeignKey('Adherent', on_delete=models.CASCADE, related_name='inscriptions_seance')
    date_inscription = models.DateTimeField(auto_now_add=True)
    covoiturage = models.CharField(max_length=10, choices=COVOITURAGE_CHOICES, blank=True, null=True, verbose_name="Covoiturage")
    lieu_covoiturage = models.CharField(max_length=200, blank=True, null=True, verbose_name="Lieu de prise en charge du covoiturage")
    class Meta:
        unique_together = ('seance', 'personne')
    def __str__(self):
        return f"{self.personne} inscrit à {self.seance} le {self.date_inscription}"

class PalanqueeEleve(models.Model):
    APTITUDE_CHOICES = [
        ('PE12', 'PE12'),
        ('PE20', 'PE20'),
        ('PA20', 'PA20'),
        ('PE40', 'PE40'),
        ('PA40', 'PA40'),
        ('PA60', 'PA60'),
        ('GP', 'GP'),
        ('E1', 'E1'),
        ('E2', 'E2'),
        ('E3', 'E3'),
        ('E4', 'E4'),
    ]
    palanquee = models.ForeignKey('Palanquee', on_delete=models.CASCADE)
    eleve = models.ForeignKey('Adherent', on_delete=models.CASCADE)
    aptitude = models.CharField(max_length=10, choices=APTITUDE_CHOICES, blank=True)
    class Meta:
        unique_together = ('palanquee', 'eleve')

class EvaluationExercice(models.Model):
    palanquee = models.ForeignKey(Palanquee, on_delete=models.CASCADE, related_name='evaluations_exercices')
    eleve = models.ForeignKey(Adherent, on_delete=models.CASCADE, related_name='evaluations_exercices_recues', limit_choices_to={'statut': 'eleve'})
    exercice = models.ForeignKey(Exercice, on_delete=models.CASCADE, related_name='evaluations')
    encadrant = models.ForeignKey(Adherent, on_delete=models.CASCADE, related_name='evaluations_exercices_donnees', limit_choices_to={'statut': 'encadrant'})
    note = models.IntegerField(choices=[(1, 'Non maîtrisé'), (2, 'En cours d’acquisition'), (3, 'Maîtrisé')])
    commentaire = models.TextField(blank=True)
    date_evaluation = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Évaluation exercice"
        verbose_name_plural = "Évaluations exercices"
        unique_together = ['eleve', 'exercice']
    
    def __str__(self):
        return f"{self.eleve.nom_complet} - {self.exercice.nom} : {self.note} étoiles"
