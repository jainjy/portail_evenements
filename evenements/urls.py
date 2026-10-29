from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Public
    path("", views.liste_evenements, name="liste_evenements"),
    path("evenements/<int:pk>/", views.detail_evenement, name="detail_evenement"),
    path("compte/creer/", views.creer_compte, name="creer_compte"),
    path("connexion/", auth_views.LoginView.as_view(), name="connexion"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),
    # Utilisateur authentifié
    path("evenements/<int:pk>/inscription/", views.s_inscrire, name="s_inscrire"),
    path("mes-inscriptions/", views.mes_inscriptions, name="mes_inscriptions"),
    path("inscriptions/<int:pk>/annuler/", views.annuler_inscription, name="annuler_inscription"),
    # Gestionnaire
    path("gestion/", views.gestion_evenements, name="gestion_evenements"),
    path("gestion/nouveau/", views.creer_evenement, name="creer_evenement"),
    path("gestion/<int:pk>/modifier/", views.modifier_evenement, name="modifier_evenement"),
    path("gestion/<int:pk>/inscrits/", views.inscrits_evenement, name="inscrits_evenement"),
]
