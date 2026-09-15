from datetime import datetime, timedelta

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from .models import LienEvaluation
from django.templatetags.static import static
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from functools import wraps


def calculer_date_expiration_lien_inscription_defaut(seance):
    """Date d'expiration par défaut : mercredi précédant la séance, à 23:59."""
    seance_date = seance.date
    weekday = seance_date.weekday()  # 0=lundi, 2=mercredi
    days_since_wed = (weekday - 2) % 7
    expiration_date = seance_date - timedelta(days=days_since_wed)
    return timezone.make_aware(
        datetime.combine(
            expiration_date,
            datetime.max.time().replace(hour=23, minute=59, second=0, microsecond=0),
        )
    )


def envoyer_lien_evaluation(lien_evaluation, request=None):
    """
    Envoie un email avec le lien d'évaluation à l'encadrant
    """
    seance = lien_evaluation.palanquee.seance
    encadrant = lien_evaluation.palanquee.encadrant
    
    # Construire l'URL complète du lien
    if request:
        lien_complet = request.build_absolute_uri(reverse('evaluation_publique', kwargs={'token': lien_evaluation.token}))
    else:
        lien_complet = f"{settings.SITE_URL}{reverse('evaluation_publique', kwargs={'token': lien_evaluation.token})}"
    
    # Préparer le contexte pour le template
    context = {
        'seance': seance,
        'encadrant': encadrant,
        'palanquee': lien_evaluation.palanquee,
        'lien': lien_evaluation,
        'lien_complet': lien_complet,
        'site_name': getattr(settings, 'SITE_NAME', 'Aquadémie Paris Plongée'),
    }
    
    # Rendre le template HTML
    html_content = render_to_string('gestion/email_lien_evaluation.html', context)
    text_content = strip_tags(html_content)
    
    # Préparer l'email
    subject = f"Lien d'évaluation - Séance du {seance.date.strftime('%d/%m/%Y')} - {lien_evaluation.palanquee.nom}"
    
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


def get_adherent_profile(user):
    """Retourne le profil adhérent lié à l'utilisateur, ou None."""
    if not user or not user.is_authenticated:
        return None
    return getattr(user, 'adherent_profile', None)


def is_ma_fiche(user, adherent_id):
    """True si adherent_id correspond au profil lié à l'utilisateur."""
    adherent = get_adherent_profile(user)
    try:
        return bool(adherent and adherent.id == int(adherent_id))
    except (TypeError, ValueError):
        return False


def is_eleve_restreint(user):
    """
    Élève « simple » : compte élève sans droits admin/codir/superuser.
    Accès limité à sa fiche, sa modification et son suivi de formation.
    """
    if not user or not user.is_authenticated or user.is_superuser:
        return False
    if user.groups.filter(name__in=['admin', 'codir']).exists():
        return False
    if user.groups.filter(name='eleve').exists():
        return True
    adherent = get_adherent_profile(user)
    return bool(adherent and adherent.statut == 'eleve')


def redirect_eleve_home(user):
    """Redirige un élève vers sa fiche adhérent (ou le login si pas de profil)."""
    adherent = get_adherent_profile(user)
    if adherent:
        return redirect('adherent_detail', pk=adherent.id)
    return redirect('login')


def peut_acceder_fiche_adherent(user, adherent_id):
    """
    - admin/codir/superuser : toutes les fiches
    - chacun : sa propre fiche
    - encadrant : fiches des élèves
    """
    if not user.is_authenticated:
        return False
    if can_access_dashboard(user):
        return True
    if is_ma_fiche(user, adherent_id):
        return True
    if user.groups.filter(name='encadrant').exists():
        from .models import Adherent
        return Adherent.objects.filter(pk=adherent_id, statut='eleve').exists()
    return False


def peut_modifier_fiche_adherent(user, adherent_id):
    """
    - admin/superuser : toutes les fiches
    - élève / encadrant / codir(+élève|encadrant) : uniquement sa propre fiche
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.groups.filter(name='admin').exists():
        return True
    return is_ma_fiche(user, adherent_id)


def formulaire_fiche_restreint(user, adherent_id=None):
    """
    Formulaire sans champs réservés admin, pour l'auto-édition
    (élève, encadrant, codir sur sa propre fiche).
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.groups.filter(name='admin').exists():
        return False
    if adherent_id is None:
        return get_adherent_profile(user) is not None
    return is_ma_fiche(user, adherent_id)


def group_required(group_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.groups.filter(name=group_name).exists() or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            # Redirection selon le groupe
            if request.user.groups.filter(name='codir').exists():
                return redirect('dashboard')
            elif is_eleve_restreint(request.user):
                return redirect_eleve_home(request.user)
            elif request.user.groups.filter(name='encadrant').exists():
                return redirect('eleve_list')
            else:
                return redirect('dashboard')
        return _wrapped_view
    return decorator

def eleve_only(view_func):
    return group_required('eleve')(view_func)

def encadrant_only(view_func):
    return group_required('encadrant')(view_func)

def admin_only(view_func):
    return group_required('admin')(view_func)

def codir_only(view_func):
    return group_required('codir')(view_func)

def is_codir(user):
    """Vérifie si l'utilisateur appartient au groupe Codir"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='codir').exists()

def is_codir_eleve(user):
    """Vérifie si l'utilisateur est à la fois Codir et élève"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='codir').exists() and user.groups.filter(name='eleve').exists()

def is_codir_encadrant(user):
    """Vérifie si l'utilisateur est à la fois Codir et encadrant"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name='codir').exists() and user.groups.filter(name='encadrant').exists()

def can_access_dashboard(user):
    """Vérifie si l'utilisateur peut accéder au dashboard"""
    if not user.is_authenticated:
        return False
    return (user.is_superuser or 
            user.groups.filter(name='admin').exists() or 
            user.groups.filter(name='codir').exists())
