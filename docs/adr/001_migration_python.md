# ADR-001 : Migration du backend Laravel vers Python FastAPI

**Statut** : Accepté  
**Date** : 2025-01-15  
**Auteur** : Équipe Backend  
**Réviseurs** : Lead Tech, DevOps, Product Owner

---

## Contexte

Le backend actuel est un monolithe **Laravel 11** composé de 32 modules Nwidart et exposant environ **290 endpoints REST**. Cette architecture a été choisie à l'origine pour sa productivité initiale, mais présente aujourd'hui plusieurs contraintes :

- **Performance** : les endpoints critiques (liste médecins, créneaux disponibles) répondent en 400–800 ms sous charge modérée (50 req/s), contre un objectif de < 200 ms.
- **Scalabilité** : le modèle PHP synchrone nécessite un processus par requête, rendant le scaling horizontal coûteux (chaque pod = 4 workers FPM minimum).
- **Testabilité** : la base de code Laravel accumule des couplages entre modules (Eloquent global state, Facades), rendant les tests unitaires difficiles sans bootstrapper le framework complet.
- **Compétences équipe** : l'équipe dispose d'une forte expertise Python/FastAPI et souhaite aligner la stack backend sur celle de l'équipe data/ML.
- **Observabilité** : instrumentation Prometheus native limitée sous Laravel sans paquets tiers.

## Décision

Migrer le backend vers **FastAPI** (Python 3.12) avec **SQLAlchemy 2.0** (mode asyncio) en utilisant le pattern **Strangler Fig** via Nginx comme API Gateway.

### Stack retenue

| Composant | Choix | Raison |
|---|---|---|
| Framework web | FastAPI 0.115+ | OpenAPI natif, validation Pydantic v2, performances ASGI |
| ORM | SQLAlchemy 2.0 (async) | Sessions asyncio, même dialecte MySQL, migrations Alembic |
| Validation | Pydantic v2 | 5-10x plus rapide que v1, intégration native FastAPI |
| Auth | python-jose + passlib | JWT HS256/RS256, bcrypt |
| Cache | Redis via aioredis | Sessions, rate limiting, queues |
| Tests | pytest-asyncio + httpx | Tests asynchrones sans overhead |
| Observabilité | prometheus-fastapi-instrumentator | Métriques /metrics automatiques |

## Alternatives considérées

### Django + Django REST Framework (DRF)
- **Pour** : maturité, écosystème, admin intégré, ORM puissant
- **Contre** : modèle synchrone par défaut (WSGI), boilerplate important, performances inférieures à FastAPI sur benchmarks I/O-bound, OpenAPI généré moins précis

### Django Ninja
- **Pour** : OpenAPI natif sur Django, validation Pydantic, compatibilité Django ORM
- **Contre** : projet moins mature (< 3 ans), communauté plus petite, toujours lié au modèle Django synchrone

### Litestar (ex-Starlite)
- **Pour** : ASGI natif, validation attrs/msgspec, performances excellentes
- **Contre** : communauté très petite, documentation en construction, risque de pérennité

### Conserver Laravel avec optimisations
- **Pour** : zéro migration, équipe déjà formée
- **Contre** : n'adresse pas les contraintes de performance, coût de scaling élevé, dette technique persistante

## Conséquences

### Positives
- **Performance** : latence P99 cible < 200 ms grâce au modèle async (I/O non-bloquant)
- **Scalabilité** : pods sans état, scaling horizontal par réplication pure
- **Observabilité** : métriques Prometheus exposées nativement sur `/metrics`
- **Développement** : OpenAPI auto-généré, validation stricte dès l'entrée, tests unitaires sans framework
- **Homogénéité** : stack Python alignée sur les équipes data/ML
- **Coût infra** : réduction estimée à 40% des ressources compute (benchmark interne)

### Négatives
- **Risque de migration** : 290 endpoints à réécrire, risque de régressions fonctionnelles
- **Période de transition** : maintien temporaire des deux backends (coût opérationnel × 2)
- **Courbe d'apprentissage** : asyncio Python pour les développeurs habitués au modèle synchrone
- **Perte de fonctionnalités Laravel** : jobs/queues, broadcasting, Horizon → à remplacer (Celery, ARQ)

## Critères de succès

- [ ] 100% des endpoints migrés et couverts par des tests API
- [ ] P99 < 200 ms sous 200 utilisateurs simultanés (Locust)
- [ ] Taux d'erreur < 1% pendant 7 jours post-déploiement production
- [ ] UAT validé par l'équipe produit et 3 cliniques pilotes
- [ ] Zéro donnée perdue lors de la migration (vérifiée par `verify_migration.py`)
