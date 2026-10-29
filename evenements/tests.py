from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import EvenementForm
from .models import Evenement, Inscription


def creer_evenement(jours=5, capacite=2, titre="Atelier test"):
    return Evenement.objects.create(
        titre=titre, description="desc", lieu="Salle",
        date_evenement=timezone.now() + timedelta(days=jours), capacite=capacite,
    )


class ValidationDonneesTests(TestCase):
    """1. Validation des données."""

    def donnees(self, **extra):
        d = {"titre": "X", "description": "d", "lieu": "L", "categorie": "atelier", "capacite": 10,
             "date_evenement": (timezone.localtime() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M")}
        d.update(extra)
        return d

    def test_formulaire_valide(self):
        self.assertTrue(EvenementForm(self.donnees()).is_valid())

    def test_capacite_nulle_refusee(self):
        self.assertIn("capacite", EvenementForm(self.donnees(capacite=0)).errors)

    def test_date_passee_refusee(self):
        passe = (timezone.localtime() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        self.assertIn("date_evenement", EvenementForm(self.donnees(date_evenement=passe)).errors)


class ReglesMetierTests(TestCase):
    """2. Règles propres au thème."""

    def setUp(self):
        self.u1 = User.objects.create_user("u1", password="x-test-1")
        self.u2 = User.objects.create_user("u2", password="x-test-2")
        self.u3 = User.objects.create_user("u3", password="x-test-3")

    def test_places_restantes_comptent_seulement_les_confirmees(self):
        ev = creer_evenement(capacite=2)
        ins = ev.inscrire(self.u1)
        self.assertEqual(ev.places_restantes, 1)
        ins.annuler()
        self.assertEqual(ev.places_restantes, 2)

    def test_refus_si_capacite_atteinte(self):
        ev = creer_evenement(capacite=1)
        ev.inscrire(self.u1)
        with self.assertRaises(ValidationError):
            ev.inscrire(self.u2)

    def test_refus_si_evenement_passe(self):
        ev = creer_evenement(jours=-1)
        with self.assertRaises(ValidationError):
            ev.inscrire(self.u1)

    def test_pas_de_double_inscription(self):
        ev = creer_evenement()
        ev.inscrire(self.u1)
        with self.assertRaises(ValidationError):
            ev.inscrire(self.u1)
        self.assertEqual(Inscription.objects.filter(evenement=ev, utilisateur=self.u1).count(), 1)

    def test_annulation_impossible_apres_debut(self):
        ev = creer_evenement(jours=1)
        ins = ev.inscrire(self.u1)
        Evenement.objects.filter(pk=ev.pk).update(date_evenement=timezone.now() - timedelta(hours=1))
        ins.refresh_from_db()
        with self.assertRaises(ValidationError):
            ins.annuler()

    def test_reinscription_apres_annulation(self):
        ev = creer_evenement()
        ev.inscrire(self.u1).annuler()
        ev.inscrire(self.u1)
        self.assertEqual(ev.places_restantes, ev.capacite - 1)


class AccesTests(TestCase):
    """3. Restrictions d'accès."""

    def setUp(self):
        self.ev = creer_evenement()
        self.user = User.objects.create_user("user", password="x-test-u")
        self.autre = User.objects.create_user("autre", password="x-test-a")
        self.staff = User.objects.create_user("staff", password="x-test-s", is_staff=True)

    def test_visiteur_voit_les_pages_publiques(self):
        self.assertEqual(self.client.get(reverse("liste_evenements")).status_code, 200)
        self.assertEqual(self.client.get(reverse("detail_evenement", args=[self.ev.pk])).status_code, 200)

    def test_visiteur_redirige_vers_connexion(self):
        for nom, args in (("mes_inscriptions", []), ("gestion_evenements", [])):
            r = self.client.get(reverse(nom, args=args))
            self.assertEqual(r.status_code, 302)
            self.assertIn(reverse("connexion"), r.url)
        r = self.client.post(reverse("s_inscrire", args=[self.ev.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.ev.inscriptions.count(), 0)

    def test_inscription_exige_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("s_inscrire", args=[self.ev.pk])).status_code, 405)

    def test_utilisateur_simple_interdit_de_gestion(self):
        self.client.force_login(self.user)
        for nom, args in (("gestion_evenements", []), ("creer_evenement", []),
                          ("modifier_evenement", [self.ev.pk]), ("inscrits_evenement", [self.ev.pk])):
            self.assertEqual(self.client.get(reverse(nom, args=args)).status_code, 403, nom)

    def test_gestionnaire_acces_autorise(self):
        self.client.force_login(self.staff)
        for nom, args in (("gestion_evenements", []), ("creer_evenement", []),
                          ("modifier_evenement", [self.ev.pk]), ("inscrits_evenement", [self.ev.pk])):
            self.assertEqual(self.client.get(reverse(nom, args=args)).status_code, 200, nom)

    def test_impossible_d_annuler_l_inscription_d_un_autre(self):
        ins = self.ev.inscrire(self.autre)
        self.client.force_login(self.user)
        r = self.client.post(reverse("annuler_inscription", args=[ins.pk]))
        self.assertEqual(r.status_code, 404)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.CONFIRMEE)

    def test_utilisateur_annule_sa_propre_inscription(self):
        ins = self.ev.inscrire(self.user)
        self.client.force_login(self.user)
        self.client.post(reverse("annuler_inscription", args=[ins.pk]))
        ins.refresh_from_db()
        self.assertEqual(ins.statut, Inscription.Statut.ANNULEE)
