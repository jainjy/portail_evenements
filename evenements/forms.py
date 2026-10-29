"""Formulaires validés côté serveur (ModelForm)."""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Evenement


class EvenementForm(forms.ModelForm):
    class Meta:
        model = Evenement
        fields = ["titre", "description", "date_evenement", "lieu", "capacite", "categorie"]
        widgets = {
            "date_evenement": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date_evenement"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"]

    def clean_capacite(self):
        capacite = self.cleaned_data["capacite"]
        if capacite < 1:
            raise forms.ValidationError("La capacité doit être d'au moins 1.")
        # En modification, on ne peut pas descendre sous le nombre d'inscrits confirmés.
        if self.instance.pk:
            confirmes = self.instance.capacite - self.instance.places_restantes
            if capacite < confirmes:
                raise forms.ValidationError(
                    f"{confirmes} inscriptions sont déjà confirmées : capacité minimale = {confirmes}."
                )
        return capacite

    def clean_date_evenement(self):
        date = self.cleaned_data["date_evenement"]
        # Une nouvelle date doit être dans le futur (ne bloque pas l'édition d'un événement passé inchangé).
        if (not self.instance.pk or "date_evenement" in self.changed_data) and date <= timezone.now():
            raise forms.ValidationError("La date de l'événement doit être dans le futur.")
        return date


class CreationCompteForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")
