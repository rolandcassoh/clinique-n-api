# Clinique N — Backend API

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi) ![License](https://img.shields.io/badge/License-MIT-yellow)

API backend asynchrone pour la plateforme **Clinique N**, construite avec FastAPI selon les principes de l'**Architecture Hexagonale** (Ports & Adapters). Couvre 25 modules métier répartis en 5 phases.

---

## Stack technique

| Composant | Version |
|-----------|---------|
| Python | 3.12 |
| FastAPI | 0.115+ |
| SQLAlchemy | 2.0 async |
| Alembic | migrations |
| Pydantic | v2 |
| Celery + Redis | tâches asynchrones |
| MySQL | 8.0 |
| Docker / Docker Compose | déploiement local |

---

## Prérequis

- Python 3.12+
- [Poetry](https://python-poetry.org/) ou `uv`
- Docker & Docker Compose
- MySQL 8.0 (ou via Docker)
- Redis 7+

---

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/roland171993/clinique-n-backend.git
cd clinique-n-backend

# Installer les dépendances
poetry install
# ou avec uv :
uv sync
```

---

## Lancer le projet

```bash
# Lancer tous les services (API + MySQL + Redis + Celery)
docker-compose up --build

# En développement (rechargement automatique)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API est disponible sur `http://localhost:8000`
Documentation interactive : `http://localhost:8000/docs`

---

## Variables d'environnement

Copier `.env.example` en `.env` et renseigner les valeurs :

```env
# Base de données
DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/clinique_n

# Sécurité
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Redis / Celery
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=no-reply@clinique-n.com
SMTP_PASSWORD=your-smtp-password

# Stripe (paiements)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## Modules (25 modules — 5 phases)

### Phase 0 — Socle
- `auth` — Authentification JWT, rôles, permissions
- `language` — Internationalisation (i18n)
- `currency` — Gestion des devises
- `constant` — Paramètres système
- `world` — Pays, villes, régions

### Phase 1 — Entités métier core
- `clinic` — Gestion des cliniques
- `customer` — Patients / utilisateurs
- `service` — Services médicaux
- `tag` — Étiquettes / catégories
- `faq` — Foire aux questions

### Phase 2 — Opérations cliniques
- `appointment` — Prise et gestion des rendez-vous
- `encounter` — Consultations médicales
- `vital` — Signes vitaux
- `request_service` — Demandes de services
- `subscription` — Abonnements clinique

### Phase 3 — Finance
- `billing` — Facturation & paiements
- `wallet` — Portefeuille électronique
- `commission` — Commissions prestataires
- `tax` — Gestion des taxes
- `promotion` — Promotions & codes promo

### Phase 4 — Marketing & contenu
- `blog` — Articles et actualités
- `slider` — Bannières & diapositives
- `page` — Pages statiques

### Phase 5 — Logistique & produits
- `logistic` — Livraison et logistique
- `product` — Catalogue produits

---

## Tests

```bash
# Lancer tous les tests
pytest

# Avec couverture de code
pytest --cov=app --cov-report=html

# Rapport HTML disponible dans htmlcov/index.html
```

---

## Architecture hexagonale

```
app/
├── modules/
│   └── <module>/
│       ├── domain/          # Entités, value objects, règles métier
│       ├── application/     # Cas d'usage (use cases), services applicatifs
│       ├── infrastructure/  # Repositories SQLAlchemy, adapters externes
│       └── api/             # Routers FastAPI, schémas Pydantic
├── core/                    # Configuration, sécurité transversale
├── shared/                  # Utilitaires partagés
├── database.py              # Session async SQLAlchemy
├── dependencies.py          # Injection de dépendances FastAPI
└── main.py                  # Point d'entrée de l'application
```

---

## Migrations Alembic

```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "description"

# Appliquer les migrations
alembic upgrade head

# Revenir en arrière
alembic downgrade -1
```

---

## License

MIT © 2024 Clinique N
