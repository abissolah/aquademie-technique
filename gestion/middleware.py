from django.conf import settings
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from .utils import est_voyage_seul, get_adherent_profile, is_eleve_restreint, redirect_eleve_home


class EleveAccessMiddleware:
    """
    Restreint les comptes élève (non admin/codir) à leur fiche, sa modification
    et leur suivi de formation. Toute autre URL est redirigée vers leur fiche.
    """

    ALLOWED_URL_NAMES = {
        'login',
        'logout',
        'password_reset',
        'password_reset_done',
        'password_reset_confirm',
        'password_reset_complete',
        'adherent_detail',
        'adherent_update',
        'suivi_formation_eleve',
        'suivi_formation_eleve_pdf',
        'suivi_evaluations_exercices_eleve_pdf',
        # Liens publics d'inscription aux séances (fosse / sorties)
        'inscription_seance_uuid',
        'api_membres_app',
        'api_inscrire_membre_app',
        'api_recherche_non_membre',
        'api_liste_non_adherents_actifs',
        'api_details_non_adherent',
        'api_inscrire_non_membre',
    }

    OWN_PK_URL_NAMES = {
        'adherent_detail',
        'adherent_update',
    }

    OWN_ELEVE_ID_URL_NAMES = {
        'suivi_formation_eleve',
        'suivi_formation_eleve_pdf',
        'suivi_evaluations_exercices_eleve_pdf',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_restrict(request):
            return redirect_eleve_home(request.user)
        return self.get_response(request)

    def _should_restrict(self, request):
        user = request.user
        if not is_eleve_restreint(user):
            return False

        path = request.path_info or '/'
        static_url = getattr(settings, 'STATIC_URL', '/static/') or '/static/'
        media_url = getattr(settings, 'MEDIA_URL', '/media/') or '/media/'
        if path.startswith(static_url) or path.startswith(media_url):
            return False

        try:
            match = resolve(path)
        except Resolver404:
            return True

        url_name = match.url_name
        if url_name is None or url_name not in self.ALLOWED_URL_NAMES:
            return True

        adherent = get_adherent_profile(user)
        if not adherent:
            return True

        if url_name in self.OWN_PK_URL_NAMES:
            pk = match.kwargs.get('pk')
            return pk is None or int(pk) != adherent.id

        if url_name in self.OWN_ELEVE_ID_URL_NAMES:
            eleve_id = match.kwargs.get('eleve_id')
            return eleve_id is None or int(eleve_id) != adherent.id

        return False


class VoyageAccessMiddleware:
    """
    Restreint le profil voyage (sans droit admin/codir) à la liste des adhérents
    du club, leurs fiches, la communication et l'export.
    """

    ALLOWED_URL_NAMES = {
        'login',
        'logout',
        'password_reset',
        'password_reset_done',
        'password_reset_confirm',
        'password_reset_complete',
        'adherent_list',
        'adherent_detail',
        'export_adherents_excel',
        'adherents_communiquer',
        'exporter_destinataires_adherents_excel',
        'supprimer_historique_mail_adherents',
        'supprimer_liste_diffusion',
        'supprimer_modele_mail_adherents',
        'api_modele_mail_adherents',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_restrict(request):
            return redirect('adherent_list')
        return self.get_response(request)

    def _should_restrict(self, request):
        if not est_voyage_seul(request.user):
            return False

        path = request.path_info or '/'
        static_url = getattr(settings, 'STATIC_URL', '/static/') or '/static/'
        media_url = getattr(settings, 'MEDIA_URL', '/media/') or '/media/'
        if (
            path.startswith(static_url)
            or path.startswith(media_url)
            or path.startswith('/ckeditor/')
            or path.startswith('/admin/')
        ):
            return False

        try:
            match = resolve(path)
        except Resolver404:
            return True

        return match.url_name not in self.ALLOWED_URL_NAMES
