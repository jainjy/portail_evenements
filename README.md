# Portail d'inscriptions à des événements (Django)

Projet M1 Informatique — Thème 1. Django + SQLite, aucun service externe.

## 1. Installation
```bash
cd portail_evenements
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Base de données
```bash
python manage.py makemigrations evenements
python manage.py migrate
```

## 3. Comptes
Gestionnaire (staff + accès à /admin/) :
```bash
python manage.py createsuperuser
```
Un utilisateur normal se crée via « Créer un compte » sur le site.

Données de démo (sans mot de passe dans le code) :
```bash
python manage.py charger_demo
```
Crée `organisateur` (staff) et `participant`, plus 4 événements.
Le mot de passe est lu dans la variable `DEMO_PASSWORD` ou généré et affiché une fois.

## 4. Lancer le serveur
```bash
python manage.py runserver
```
Site : http://127.0.0.1:8000/ — Admin : http://127.0.0.1:8000/admin/

## 5. Tests
```bash
python manage.py test
```

## Rôles
| Rôle | Accès |
|---|---|
| Visiteur | Liste (recherche, filtre, pagination), détail |
| Utilisateur | S'inscrire, mes inscriptions, annuler (avant le début) |
| Gestionnaire (`is_staff`) | Créer/modifier événements, liste des inscrits |

## Sécurité
- Toute modification passe par `POST` + jeton CSRF.
- `annuler_inscription` filtre sur `utilisateur=request.user` (404 sinon).
- Vues de gestion : décorateur `gestionnaire_requis` (anonyme → connexion, non-staff → 403).
- En production : définir `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`.

## Tailwind CSS
Géré par le paquet **django-tailwind** (Node.js / npm, **pas** le binaire autonome).
Prérequis : Node.js et npm installés (https://nodejs.org).

Le CSS compilé (`theme/static/css/dist/styles.css`) est fourni : le site fonctionne sans rien faire.
Pour modifier le style :
```bash
python manage.py tailwind install   # installe les dépendances npm (première fois)
python manage.py tailwind build     # compile une fois
python manage.py tailwind start    # recompile à chaque modification
```
Source : `css_src/input.css` (et les templates).
