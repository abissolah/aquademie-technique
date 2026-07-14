from django.core.files.base import ContentFile


def copier_fichier_champ(source_field, dest_instance, dest_attr):
    """Copie le contenu d'un FileField/ImageField vers un autre modèle."""
    if not source_field:
        return
    source_field.open('rb')
    try:
        contenu = source_field.read()
    finally:
        source_field.close()
    nom = source_field.name.split('/')[-1]
    getattr(dest_instance, dest_attr).save(nom, ContentFile(contenu), save=False)


def prefill_adherent_depuis_ancien(adherent, ancien):
    """Préremplit un adhérent (non sauvegardé) à partir d'un ancien adhérent."""
    adherent.ancien_adherent = ancien
    adherent.nom = ancien.nom
    adherent.prenom = ancien.prenom
    adherent.date_naissance = ancien.date_naissance
    adherent.adresse = ancien.adresse
    adherent.code_postal = ancien.code_postal
    adherent.ville = ancien.ville
    adherent.email = ancien.email
    adherent.telephone = ancien.telephone
    adherent.numero_licence = ancien.numero_licence or ''
    adherent.assurance = ancien.assurance or ''
    adherent.date_delivrance_caci = ancien.date_delivrance_caci
    adherent.niveau = ancien.niveau
    adherent.statut = ancien.statut
    adherent.type_personne = 'adherent'
    adherent.caci_valide = False
    adherent.inscription_hello_asso = False
    adherent.actif = True


def appliquer_photo_depuis_ancien(adherent, ancien):
    """Copie la photo de l'ancien adhérent si aucune nouvelle photo n'a été fournie."""
    if adherent.photo or not ancien or not ancien.photo:
        return
    copier_fichier_champ(ancien.photo, adherent, 'photo')
