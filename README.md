# 🏥 Clinique N - API Backend (FastAPI)

API REST pour le système de gestion de clinique médicale numérique.

## 🚀 Technologies

- **Framework** : FastAPI 0.115.6
- **Langage** : Python 3.12.8
- **Base de données** : MySQL 8.4.3 avec SQLAlchemy 2.0 (async)
- **Cache** : Redis 7.4.1
- **Queue** : Celery 5.4.0
- **Recherche** : Meilisearch 1.11.3
- **Conteneurisation** : Docker & Docker Compose

## 📁 Structure du Projet

```
python-api/
├── app/
│   ├── core/              # Infrastructure transversale
│   │   ├── auth/          # JWT, OAuth, TOTP
│   │   ├── cache/         # Abstraction Redis
│   │   ├── middleware/    # RBAC, logging, CORS
│   │   └── ...
│   ├── modules/           # Modules métier
│   │   ├── auth/
│   │   ├── clinic/
│   │   ├── rendez_vous/
│   │   ├── consultation/
│   │   ├── facturation/
│   │   └── ...
│   ├── shared/            # Code partagé
│   ├── main.py           # Point d'entrée FastAPI
│   ├── config.py         # Configuration Pydantic
│   └── celery_app.py     # Configuration Celery
├── alembic/              # Migrations de base de données
├── tests/                # Tests unitaires et d'intégration
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml        # Dépendances Poetry

```

## 🛠️ Installation et Démarrage

### Prérequis
- Docker Engine 20.10+
- Docker Compose 2.0+

### Démarrage rapide

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-organisation/clinique-n-api.git
cd clinique-n-api

# 2. Copier le fichier d'environnement
cp .env.example .env

# 3. Démarrer tous les services
docker compose up -d

# 4. Vérifier la santé
./check_health.sh
```

### Services disponibles

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | API REST principale |
| Swagger UI | http://localhost:8000/docs | Documentation interactive |
| ReDoc | http://localhost:8000/redoc | Documentation alternative |
| MailHog | http://localhost:8025 | Interface de test email |
| Meilisearch | http://localhost:7700 | Interface de recherche |
| MySQL | localhost:3309 | Base de données |
| Redis | localhost:6379 | Cache et broker |

## 📚 Documentation

- [Guide de déploiement](DEPLOYMENT.md)
- [Changelog](CHANGELOG.md)
- [Documentation API](http://localhost:8000/docs) (après démarrage)

## 🧪 Tests

```bash
# Lancer tous les tests
docker compose exec api pytest

# Tests avec couverture
docker compose exec api pytest --cov=app --cov-report=html

# Tests d'un module spécifique
docker compose exec api pytest tests/unit/modules/auth/
```

## 🔧 Commandes Utiles

### Gestion des conteneurs

```bash
# Démarrer les services
docker compose up -d

# Arrêter les services
docker compose down

# Voir les logs
docker compose logs -f api

# Rebuild après modification
docker compose build api celery
docker compose up -d
```

### Base de données

```bash
# Créer une migration
docker compose exec api alembic revision --autogenerate -m "description"

# Appliquer les migrations
docker compose exec api alembic upgrade head

# Revenir en arrière
docker compose exec api alembic downgrade -1
```

### Développement

```bash
# Formater le code
docker compose exec api ruff format app

# Linter
docker compose exec api ruff check app

# Type checking
docker compose exec api mypy app
```

## 🔐 Sécurité

**⚠️ Important** : Avant le déploiement en production, modifiez les clés secrètes dans `.env` :
- `APP_SECRET_KEY`
- `JWT_SECRET_KEY`
- `ENCRYPTION_KEY`

Générez des clés sécurisées :
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 🌍 Variables d'Environnement

Voir `.env.example` pour la liste complète des variables configurables.

## 📊 Architecture

L'API suit une architecture en couches :

1. **API Layer** (FastAPI routers) : Points d'entrée HTTP
2. **Application Layer** (Use Cases) : Logique métier
3. **Domain Layer** : Entités et règles métier
4. **Infrastructure Layer** : Accès aux données (SQLAlchemy)

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -m 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request

## 📝 Conventions

- **Langue du code** : Français (variables, fonctions, commentaires)
- **Style** : PEP 8 avec Ruff
- **Type hints** : Obligatoires (mypy strict)
- **Tests** : Couverture minimale de 85%

## 📄 Licence

Propriétaire - Tous droits réservés © 2026 Clinique N

## 👥 Équipe

- **Architecture** : Équipe Backend Clinique N
- **Développement** : Contributeurs Clinique N

## 📞 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Contact : support@clinique-n.com

---

**Version** : 0.1.0  
**Dernière mise à jour** : Juin 2026
