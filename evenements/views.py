"""Vues : publiques, utilisateur authentifié et gestionnaire."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import CreationCompteForm, EvenementForm
from .models import Evenement, Inscription


def gestionnaire_requis(vue):
    """Réserve la vue au staff : anonyme → connexion, non-staff → 403."""

    @wraps(vue)
    def _vue(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_staff:
            raise PermissionDenied
        return vue(request, *args, **kwargs)

    return _vue


# ---------- Pages publiques ----------
def liste_evenements(request):
    """Événements à venir, recherche par titre, filtre par catégorie, pagination."""
    evenements = Evenement.objects.filter(date_evenement__gt=timezone.now())
    q = request.GET.get("q", "").strip()
    categorie = request.GET.get("categorie", "")
    if q:
        evenements = evenements.filter(titre__icontains=q)
    if categorie in Evenement.Categorie.values:
        evenements = evenements.filter(categorie=categorie)
    page = Paginator(evenements, 6).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "evenements/liste_evenements.html", {
        "page": page, "q": q, "categorie": categorie,
        "categories": Evenement.Categorie.choices, "querystring": params.urlencode(),
    })


def detail_evenement(request, pk):
    evenement = get_object_or_404(Evenement, pk=pk)
    inscription = None
    if request.user.is_authenticated:
        inscription = Inscription.objects.filter(evenement=evenement, utilisateur=request.user).first()
    return render(request, "evenements/detail_evenement.html", {
        "evenement": evenement, "inscription": inscription,
        "deja_inscrit": bool(inscription and inscription.statut == Inscription.Statut.CONFIRMEE),
    })


def creer_compte(request):
    form = CreationCompteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Compte créé, bienvenue !")
        return redirect("liste_evenements")
    return render(request, "registration/creer_compte.html", {"form": form})


# ---------- Utilisateur authentifié ----------
@login_required
@require_POST
def s_inscrire(request, pk):
    evenement = get_object_or_404(Evenement, pk=pk)
    try:
        evenement.inscrire(request.user)
        messages.success(request, f"Inscription confirmée à « {evenement.titre} ».")
    except ValidationError as e:
        messages.error(request, " ".join(e.messages))
    return redirect("detail_evenement", pk=pk)


@login_required
def mes_inscriptions(request):
    inscriptions = Inscription.objects.filter(utilisateur=request.user).select_related("evenement")
    return render(request, "evenements/mes_inscriptions.html", {"inscriptions": inscriptions})


@login_required
@require_http_methods(["GET", "POST"])
def annuler_inscription(request, pk):
    # Filtrer par utilisateur : on ne peut jamais toucher l'inscription d'un autre (404).
    inscription = get_object_or_404(
        Inscription.objects.select_related("evenement"), pk=pk, utilisateur=request.user
    )
    if request.method == "POST":
        try:
            inscription.annuler()
            messages.success(request, "Votre inscription a été annulée.")
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))
        return redirect("mes_inscriptions")
    # GET : page de confirmation visuelle
    return render(request, "evenements/confirmer_annulation.html", {"inscription": inscription})


# ---------- Gestionnaire ----------
@gestionnaire_requis
def gestion_evenements(request):
    return render(request, "evenements/gestion_evenements.html", {
        "evenements": Evenement.objects.order_by("-date_evenement")
    })


@gestionnaire_requis
def creer_evenement(request):
    form = EvenementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        evenement = form.save()
        messages.success(request, f"Événement « {evenement.titre} » créé.")
        return redirect("gestion_evenements")
    return render(request, "evenements/formulaire_evenement.html", {"form": form, "titre_page": "Nouvel événement"})


@gestionnaire_requis
def modifier_evenement(request, pk):
    evenement = get_object_or_404(Evenement, pk=pk)
    form = EvenementForm(request.POST or None, instance=evenement)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Événement modifié.")
        return redirect("gestion_evenements")
    return render(request, "evenements/formulaire_evenement.html", {"form": form, "titre_page": "Modifier l'événement"})


@gestionnaire_requis
def inscrits_evenement(request, pk):
    evenement = get_object_or_404(Evenement, pk=pk)
    inscriptions = evenement.inscriptions.select_related("utilisateur")
    return render(request, "evenements/inscrits_evenement.html", {
        "evenement": evenement, "inscriptions": inscriptions
    })
