from .utils import (
    can_access_dashboard,
    get_adherent_profile,
    is_codir,
    is_eleve_restreint,
)


def user_roles(request):
    """Expose les rôles utiles dans tous les templates."""
    user = getattr(request, 'user', None)
    authenticated = bool(user and user.is_authenticated)
    adherent = get_adherent_profile(user) if authenticated else None
    return {
        'is_eleve_restreint': is_eleve_restreint(user) if authenticated else False,
        'adherent_profile': adherent,
        'is_codir_nav': is_codir(user) if authenticated else False,
        'is_encadrant_nav': bool(
            authenticated and user.groups.filter(name='encadrant').exists()
        ),
        'is_admin_nav': bool(
            authenticated and (
                user.is_superuser or user.groups.filter(name='admin').exists()
            )
        ),
        'can_access_dashboard_nav': can_access_dashboard(user) if authenticated else False,
    }
