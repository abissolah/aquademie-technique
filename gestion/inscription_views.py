import json
import logging

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView

from .adherent_inscription_services import appliquer_photo_depuis_ancien
from .forms import AdherentPublicForm2026
from .models import Adherent, AncienAdherent

logger = logging.getLogger(__name__)

SAISON_PRECEDENTE = '2025-2026'


def inscription_saison_fermee(request):
    return render(request, 'gestion/adherent_public_inscription_fermee.html', {
        'saison_fermee': '2025-2026',
        'nouvelle_url': reverse('adherent_public_inscription_etape1'),
    })


def inscription_saison_etape1(request):
    return render(request, 'gestion/adherent_public_inscription_etape1.html', {
        'saison_precedente': SAISON_PRECEDENTE,
        'saison_courante': '2026-2027',
    })


@require_GET
def api_recherche_anciens_adherents(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    mots = q.split()
    queryset = AncienAdherent.objects.filter(saison=SAISON_PRECEDENTE)
    for mot in mots:
        queryset = queryset.filter(Q(nom__icontains=mot) | Q(prenom__icontains=mot))
    results = [
        {
            'id': a.pk,
            'label': f'{a.nom.upper()} {a.prenom.capitalize()} — né(e) le {a.date_naissance.strftime("%d/%m/%Y")}',
            'nom': a.nom,
            'prenom': a.prenom,
        }
        for a in queryset.order_by('nom', 'prenom')[:25]
    ]
    return JsonResponse({'results': results})


@require_GET
def api_recherche_adherents_en_cours(request):
    """Recherche les adhérents déjà inscrits mais sans Hello Asso validé."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    mots = q.split()
    queryset = Adherent.objects.filter(
        type_personne='adherent',
        inscription_hello_asso=False,
        actif=True,
    )
    for mot in mots:
        queryset = queryset.filter(Q(nom__icontains=mot) | Q(prenom__icontains=mot))
    results = [
        {
            'id': a.pk,
            'label': f'{a.nom.upper()} {a.prenom.capitalize()} — né(e) le {a.date_naissance.strftime("%d/%m/%Y")}',
            'nom': a.nom,
            'prenom': a.prenom,
        }
        for a in queryset.order_by('nom', 'prenom')[:25]
    ]
    return JsonResponse({'results': results})


@method_decorator(csrf_protect, name='dispatch')
class AdherentPublicCreateView2026(CreateView):
    model = Adherent
    form_class = AdherentPublicForm2026
    template_name = 'gestion/adherent_public_form_2026_2027.html'

    def get_ancien_adherent(self):
        ancien_id = self.request.GET.get('ancien_id') or self.request.POST.get('ancien_adherent_id')
        if not ancien_id:
            return None
        return AncienAdherent.objects.filter(pk=ancien_id, saison=SAISON_PRECEDENTE).first()

    def get_adherent_en_cours(self):
        adherent_id = self.request.GET.get('adherent_id') or self.request.POST.get('adherent_id')
        if not adherent_id:
            return None
        return Adherent.objects.filter(
            pk=adherent_id,
            type_personne='adherent',
            inscription_hello_asso=False,
        ).first()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        adherent = self.get_adherent_en_cours()
        if adherent:
            kwargs['instance'] = adherent
        kwargs['ancien_adherent'] = None if adherent else self.get_ancien_adherent()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        adherent = self.get_adherent_en_cours()
        ancien = None if adherent else self.get_ancien_adherent()
        context['ancien_adherent'] = ancien
        context['adherent_en_cours'] = adherent
        context['reprise_inscription'] = adherent is not None
        context['saison_courante'] = '2026-2027'
        context['hello_asso_url'] = getattr(settings, 'HELLO_ASSO_URL', '')
        context['inscription_success'] = kwargs.get('inscription_success', False)
        if adherent and adherent.photo:
            context['photo_ancien_url'] = adherent.photo.url
        elif ancien and ancien.photo:
            context['photo_ancien_url'] = ancien.photo.url
        if adherent and adherent.caci_fichier_effectif:
            context['caci_ancien_url'] = adherent.caci_fichier_effectif.url
        elif ancien and ancien.caci_fichier:
            context['caci_ancien_url'] = ancien.caci_fichier.url
        return context

    def form_valid(self, form):
        adherent_existant = self.get_adherent_en_cours()
        ancien = None if adherent_existant else (form.ancien_adherent or self.get_ancien_adherent())
        adherent = form.save(commit=False)

        if adherent_existant:
            if form.cleaned_data.get('caci_fichier'):
                adherent.caci_valide = False
            adherent.inscription_hello_asso = False
            adherent.actif = True
        else:
            adherent.type_personne = 'adherent'
            adherent.caci_valide = False
            adherent.inscription_hello_asso = False
            adherent.actif = True
            if ancien:
                adherent.ancien_adherent = ancien

        adherent.save()
        if not adherent_existant:
            appliquer_photo_depuis_ancien(adherent, ancien)
        if form.cleaned_data.get('photo'):
            adherent.photo = form.cleaned_data['photo']
        if form.cleaned_data.get('caci_fichier'):
            adherent.caci_fichier = form.cleaned_data['caci_fichier']
        adherent.save()
        return self.render_to_response(
            self.get_context_data(form=AdherentPublicForm2026(), inscription_success=True)
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form, inscription_success=False))


def _extraire_email_helloasso(payload):
    """Extrait un email du payload Hello Asso (structure variable selon le type d'événement)."""
    if isinstance(payload, dict):
        for key in ('email', 'payerEmail', 'PayerEmail'):
            if payload.get(key):
                return payload[key]
        for sub_key in ('data', 'order', 'payment', 'formAnswer', 'payer'):
            sub = payload.get(sub_key)
            if isinstance(sub, dict):
                email = _extraire_email_helloasso(sub)
                if email:
                    return email
        for value in payload.values():
            if isinstance(value, dict):
                email = _extraire_email_helloasso(value)
                if email:
                    return email
    return None


@csrf_exempt
@require_POST
def helloasso_webhook(request):
    secret_attendu = getattr(settings, 'HELLO_ASSO_WEBHOOK_SECRET', '')
    if secret_attendu:
        secret_recu = request.headers.get('X-HelloAsso-Secret') or request.GET.get('secret', '')
        if secret_recu != secret_attendu:
            return HttpResponseForbidden('Secret webhook invalide')
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    email = _extraire_email_helloasso(payload)
    if not email:
        logger.warning('Webhook Hello Asso sans email identifiable: %s', payload)
        return JsonResponse({'success': False, 'error': 'Email introuvable dans le payload'}, status=422)
    updated = Adherent.objects.filter(email__iexact=email, type_personne='adherent').update(
        inscription_hello_asso=True
    )
    return JsonResponse({'success': True, 'updated': updated, 'email': email})
