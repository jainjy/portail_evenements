"""Données de démonstration. Aucun mot de passe n'est écrit dans le code :
il est lu dans DEMO_PASSWORD ou généré aléatoirement puis affiché une seule fois."""
import os
import secrets
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from evenements.models import Evenement


class Command(BaseCommand):
    help = "Crée des utilisateurs et événements de démonstration."

    def handle(self, *args, **options):
        mot_de_passe = os.environ.get("DEMO_PASSWORD") or secrets.token_urlsafe(10)
        for nom, staff in (("organisateur", True), ("participant", False)):
            user, cree = User.objects.get_or_create(
                username=nom, defaults={"email": f"{nom}@exemple.org", "is_staff": staff}
            )
            if cree:
                user.set_password(mot_de_passe)
                user.save()
                self.stdout.write(f"Utilisateur créé : {nom}")
        base = timezone.now().replace(minute=0, second=0, microsecond=0)
        demos = [
            ("Atelier Python débutant", "Initiation pratique à Python.", 5, "Salle A", 15, "atelier"),
            ("Conférence IA & société", "Enjeux de l'intelligence artificielle.", 12, "Amphi 1", 100, "conference"),
            ("Rencontre des bénévoles", "Moment convivial pour les membres.", 20, "Cour centrale", 30, "rencontre"),
            ("Atelier Django", "Construire une application web.", 30, "Salle B", 12, "atelier"),
        ]
        for titre, desc, jours, lieu, cap, cat in demos:
            Evenement.objects.get_or_create(titre=titre, defaults={
                "description": desc, "date_evenement": base + timedelta(days=jours),
                "lieu": lieu, "capacite": cap, "categorie": cat})
        self.stdout.write(self.style.SUCCESS("Données de démo prêtes."))
        self.stdout.write(f"Mot de passe des comptes créés (à noter) : {mot_de_passe}")
