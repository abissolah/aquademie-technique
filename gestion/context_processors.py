from .utils import get_adherent_profile, is_eleve_restreint


def user_roles(request):
    """Expose les rôles utiles dans tous les templates."""
    user = getattr(request, 'user', None)
    adherent = get_adherent_profile(user) if user else None
    return {
        'is_eleve_restreint': is_eleve_restreint(user) if user else False,
        'adherent_profile': adherent,
    }
