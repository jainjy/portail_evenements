"""Modèles : Evenement et Inscription, avec la logique métier des places."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class Evenement(models.Model):
    class Categorie(models.TextChoices):
        ATELIER = "atelier", "Atelier"
        CONFERENCE = "conference", "Conférence"
        RENCONTRE = "rencontre", "Rencontre"

    titre = models.CharField(max_length=200)
    description = models.TextField()
    date_evenement = models.DateTimeField("date et heure")
    lieu = models.CharField(max_length=200)
    capacite = models.PositiveIntegerField(
        "capacité", validators=[MinValueValidator(1, "La capacité doit être d'au moins 1.")]
    )
    categorie = models.CharField(
        "catégorie", max_length=20, choices=Categorie.choices, default=Categorie.ATELIER
    )

    class Meta:
        ordering = ["date_evenement"]

    def __str__(self):
        return f"{self.titre} ({self.date_evenement:%d/%m/%Y})"

    @property
    def est_passe(self):
        """Vrai si l'événement a déjà commencé."""
        return self.date_evenement <= timezone.now()

    @property
    def places_restantes(self):
        """Capacité moins le nombre d'inscriptions *confirmées* uniquement."""
        confirmees = self.inscriptions.filter(statut=Inscription.Statut.CONFIRMEE).count()
        return max(0, self.capacite - confirmees)

    @property
    def est_complet(self):
        return self.places_restantes == 0

    def inscrire(self, utilisateur):
        """Inscrit l'utilisateur ou lève ValidationError (règles métier)."""
        with transaction.atomic():
            # Verrou de ligne (ignoré par SQLite, utile sur d'autres SGBD).
            evenement = Evenement.objects.select_for_update().get(pk=self.pk)
            if evenement.est_passe:
                raise ValidationError("Cet événement a déjà commencé : inscription impossible.")
            existante = Inscription.objects.filter(evenement=evenement, utilisateur=utilisateur).first()
            if existante and existante.statut == Inscription.Statut.CONFIRMEE:
                raise ValidationError("Vous êtes déjà inscrit à cet événement.")
            if evenement.est_complet:
                raise ValidationError("Plus de places disponibles pour cet événement.")
            if existante:  # réinscription après annulation : on réactive la ligne
                existante.statut = Inscription.Statut.CONFIRMEE
                existante.save(update_fields=["statut"])
                return existante
            return Inscription.objects.create(evenement=evenement, utilisateur=utilisateur)


class Inscription(models.Model):
    class Statut(models.TextChoices):
        CONFIRMEE = "confirmee", "Confirmée"
        ANNULEE = "annulee", "Annulée"

    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name="inscriptions")
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inscriptions"
    )
    date_inscription = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.CONFIRMEE)

    class Meta:
        unique_together = ("evenement", "utilisateur")  # pas de double inscription
        ordering = ["-date_inscription"]

    def __str__(self):
        return f"{self.utilisateur} → {self.evenement.titre} [{self.get_statut_display()}]"

    def annuler(self):
        """Annule l'inscription, uniquement avant le début de l'événement."""
        if self.statut == self.Statut.ANNULEE:
            raise ValidationError("Cette inscription est déjà annulée.")
        if self.evenement.est_passe:
            raise ValidationError("Annulation impossible : l'événement a déjà commencé.")
        self.statut = self.Statut.ANNULEE
        self.save(update_fields=["statut"])
