from django.contrib import admin

from .models import Evenement, Inscription


class InscriptionInline(admin.TabularInline):
    model = Inscription
    extra = 0
    autocomplete_fields = ["utilisateur"]


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ("titre", "categorie", "date_evenement", "lieu", "capacite", "places_restantes")
    list_filter = ("categorie", "date_evenement")
    search_fields = ("titre", "lieu", "description")
    date_hierarchy = "date_evenement"
    inlines = [InscriptionInline]


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "evenement", "statut", "date_inscription")
    list_filter = ("statut", "evenement__categorie")
    search_fields = ("utilisateur__username", "evenement__titre")
    autocomplete_fields = ["utilisateur"]
