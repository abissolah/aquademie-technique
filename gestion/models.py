from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

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
    
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    adresse = models.TextField()
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    photo = models.ImageField(upload_to='photos_adherents/', blank=True, null=True)
    date_fin_validite_caci = models.DateField()
    niveau = models.CharField(max_length=20, choices=NIVEAUX_CHOICES)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='eleve')
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

class Competence(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='competences')
    
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
    
    class Meta:
        verbose_name = "Groupe de compétences"
        verbose_name_plural = "Groupes de compétences"
        ordering = ['section', 'intitule']
    
    def __str__(self):
        return f"{self.section.get_nom_display()} - {self.intitule}"

class Seance(models.Model):
    palanquee = models.CharField(max_length=200)
    date = models.DateField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='seances')
    encadrant = models.ForeignKey(Adherent, on_delete=models.CASCADE, related_name='seances_encadrees', limit_choices_to={'statut': 'encadrant'})
    eleves = models.ManyToManyField(Adherent, related_name='seances_suivies', limit_choices_to={'statut': 'eleve'})
    competences = models.ManyToManyField(Competence, related_name='seances')
    precision_exercices = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Séance"
        verbose_name_plural = "Séances"
        ordering = ['-date', 'palanquee']
    
    def __str__(self):
        return f"{self.date} - {self.palanquee} - {self.encadrant.nom_complet}"

class Evaluation(models.Model):
    seance = models.ForeignKey(Seance, on_delete=models.CASCADE, related_name='evaluations')
    eleve = models.ForeignKey(Adherent, on_delete=models.CASCADE, related_name='evaluations_recues', limit_choices_to={'statut': 'eleve'})
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='evaluations')
    note = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], help_text="0 = pas maîtrisé, 5 = parfaitement maîtrisé")
    commentaire = models.TextField(blank=True)
    date_evaluation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        unique_together = ['seance', 'eleve', 'competence']
    
    def __str__(self):
        return f"{self.seance} - {self.eleve.nom_complet} - {self.competence.nom} ({self.note}/5)"

class LienEvaluation(models.Model):
    seance = models.ForeignKey(Seance, on_delete=models.CASCADE, related_name='liens_evaluation')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
    est_valide = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Lien d'évaluation"
        verbose_name_plural = "Liens d'évaluation"
    
    def __str__(self):
        return f"Lien évaluation {self.seance} - {self.token}"
    
    @property
    def url_evaluation(self):
        return f"/evaluation/{self.token}/"
