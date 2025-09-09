from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from .models import LienEvaluation
from django.templatetags.static import static


def envoyer_lien_evaluation(lien_evaluation, request=None):
    """
    Envoie un email avec le lien d'évaluation à l'encadrant
    """
    seance = lien_evaluation.seance
    encadrant = seance.encadrant
    
    # Construire l'URL complète du lien
    if request:
        lien_complet = request.build_absolute_uri(reverse('evaluation_publique', kwargs={'token': lien_evaluation.token}))
    else:
        lien_complet = f"{settings.SITE_URL}{reverse('evaluation_publique', kwargs={'token': lien_evaluation.token})}"
    
    # Préparer le contexte pour le template
    context = {
        'seance': seance,
        'encadrant': encadrant,
        'lien': lien_evaluation,
        'lien_complet': lien_complet,
        'site_name': getattr(settings, 'SITE_NAME', 'Aquadémie Paris Plongée'),
    }
    
    # Rendre le template HTML
    html_content = render_to_string('gestion/email_lien_evaluation.html', context)
    text_content = strip_tags(html_content)
    
    # Préparer l'email
    subject = f"Lien d'évaluation - Séance du {seance.date.strftime('%d/%m/%Y')} - {seance.palanquee}"
    
    # Destinataires
    to_emails = [encadrant.email]
    cc_emails = getattr(settings, 'EMAIL_CC_DEFAULT', [])
    
    # Créer l'email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to_emails,
        cc=cc_emails
    )
    
    # Ajouter la version HTML
    email.attach_alternative(html_content, "text/html")
    
    try:
        # Envoyer l'email
        email.send()
        return True, "Email envoyé avec succès"
    except Exception as e:
        return False, f"Erreur lors de l'envoi de l'email : {str(e)}"


def envoyer_lien_evaluation_avec_cc(lien_evaluation, cc_emails=None, request=None):
    """
    Envoie un email avec le lien d'évaluation à l'encadrant avec des adresses CC personnalisées
    """
    seance = lien_evaluation.seance
    encadrant = seance.encadrant
    
    # Construire l'URL complète du lien
    if request:
        lien_complet = request.build_absolute_uri(reverse('evaluation_publique', kwargs={'token': lien_evaluation.token}))
    else:
        lien_complet = f"{settings.SITE_URL}{reverse('evaluation_publique', kwargs={'token': lien_evaluation.token})}"
    
    # Préparer le contexte pour le template
    context = {
        'seance': seance,
        'encadrant': encadrant,
        'lien': lien_evaluation,
        'lien_complet': lien_complet,
        'site_name': getattr(settings, 'SITE_NAME', 'Aquadémie Paris Plongée'),
    }
    
    # Rendre le template HTML
    html_content = render_to_string('gestion/email_lien_evaluation.html', context)
    text_content = strip_tags(html_content)
    
    # Préparer l'email
    subject = f"Lien d'évaluation - Séance du {seance.date.strftime('%d/%m/%Y')} - {seance.palanquee}"
    
    # Destinataires
    to_emails = [encadrant.email]
    
    # Adresses CC : combiner les adresses par défaut et celles fournies
    default_cc = getattr(settings, 'EMAIL_CC_DEFAULT', [])
    if cc_emails:
        all_cc = list(set(default_cc + cc_emails))  # Éviter les doublons
    else:
        all_cc = default_cc
    
    # Créer l'email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to_emails,
        cc=all_cc
    )
    
    # Ajouter la version HTML
    email.attach_alternative(html_content, "text/html")
    
    try:
        # Envoyer l'email
        email.send()
        return True, "Email envoyé avec succès"
    except Exception as e:
        return False, f"Erreur lors de l'envoi de l'email : {str(e)}" 


def get_signature_html():
    return '''
    <div style="margin-top:20px; text-align:left;">
      <img src="cid:signature_mouss2" alt="Signature Mouss" style="min-width:420px; width:420px; max-width:100%;">
    </div>
    ''' 