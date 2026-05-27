# ADR-003 : Pattern Strangler Fig via API Gateway Nginx

**Statut** : Accepté  
**Date** : 2025-02-01  
**Auteur** : Équipe DevOps  
**Réviseurs** : Lead Tech, Product Owner

---

## Contexte

Avec 290 endpoints répartis sur 32 modules Laravel, une migration "big bang" (tout réécrire, tout déployer d'un coup) était inenvisageable :

- Risque d'interruption de service pour les cliniques en production
- Impossible de valider 290 endpoints en une seule release
- En cas de bug critique, le rollback impliquerait de revenir à l'état initial complet
- L'équipe ne peut pas stopper tout développement produit pendant la migration

Il fallait une stratégie permettant de **migrer progressivement**, module par module, avec la possibilité de revenir en arrière à tout moment.

## Décision

Adopter le **pattern Strangler Fig** (Martin Fowler, 2004) en utilisant **Nginx comme API Gateway** pour router progressivement le trafic du backend Laravel vers le backend Python.

### Principe

Nginx reçoit 100% du trafic. Pour chaque endpoint migré, une règle Nginx redirige vers Python. Les endpoints non encore migrés continuent vers Laravel. Laravel est "étranglé" progressivement jusqu'à disparition.

```
                    ┌─────────────┐
Client ────────────►│    Nginx    │
                    │  (Gateway)  │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │ routing par location{}  │
              ▼                         ▼
     ┌─────────────────┐      ┌──────────────────┐
     │  Python FastAPI  │      │  Laravel (legacy) │
     │  (migré)         │      │  (fallback)       │
     └─────────────────┘      └──────────────────┘
```

### Phases de migration

| Phase | Modules | % trafic Python | Durée estimée |
|---|---|---|---|
| Phase 0 | Auth (login, register, OTP) | 5% | Semaine 1-2 |
| Phase 1 | Référentiels (countries, currencies, languages, tags, FAQ, pages) | 15% | Semaine 3-4 |
| Phase 2 | Commerce (products, orders, cart, services, shipping, taxes) | 40% | Semaine 5-8 |
| Phase 3 | Clinique (clinics, doctors, vitals, subscriptions) | 70% | Semaine 9-12 |
| Phase 4 | Médical (appointments, billing, wallet, commissions, webhooks) | 100% | Semaine 13-16 |
| Phase 5 | Décommissionnement Laravel | 100% | Semaine 17 |

### Configuration Nginx dual-stack (phases 0-4)

Voir `nginx/staging.conf` — chaque phase ajoute un bloc `location` pointant vers `upstream python_api`. Le fallback `location /api/` continue vers `upstream laravel_api`.

### Critères de passage entre phases

Avant de basculer une nouvelle phase :
1. **Couverture tests** : 100% des nouveaux endpoints couverts par des tests API (pytest + httpx)
2. **Monitoring** : 48h sans erreur 5xx sur les endpoints de la phase précédente
3. **Performance** : P99 < 200 ms mesuré par Locust (200 users, 5 min)
4. **Validation fonctionnelle** : UAT signé par le Product Owner sur au moins une clinique pilote

### Rollback en < 30 secondes

À n'importe quel moment, revenir à Laravel :

```bash
# Restaurer la config Nginx précédente
cp /etc/nginx/backup/clinique.conf.TIMESTAMP /etc/nginx/sites-available/clinique.conf
nginx -s reload  # < 1 seconde de downtime (graceful)

# Ou via le script automatisé
bash scripts/rollback_to_laravel.sh production
```

Le rollback ne nécessite aucune modification de la base de données (les deux backends partagent le même schéma MySQL pendant la transition).

## Alternatives considérées

### Migration big bang
- **Pour** : plus simple conceptuellement, pas de phase duale
- **Contre** : risque d'interruption de service total, validation impossible en une release, rollback coûteux

### Blue-Green Deployment
- **Pour** : deux environnements identiques, bascule instantanée
- **Contre** : coût infrastructure × 2, ne permet pas la migration progressive endpoint par endpoint, nécessite que 100% du code soit migré avant de basculer

### Feature flags applicatifs
- **Pour** : granularité maximale (par endpoint, par utilisateur, par clinique)
- **Contre** : complexité dans le code (flags à maintenir et nettoyer), dépendance à un service de feature flags, logique de routage dans l'application plutôt qu'à l'infrastructure

### Migration par shadow mode (traffic mirroring)
- **Pour** : valider Python en production sans impacter les clients
- **Contre** : Nginx Plus requis (payant) pour le mirroring, complexité opérationnelle, les effets de bord (écritures) ne peuvent pas être mirrorés

## Conséquences

### Positives
- **Zéro interruption de service** : les clients ne voient aucune coupure pendant la migration
- **Validation incrémentale** : chaque phase est validée indépendamment avant de passer à la suivante
- **Rollback instantané** : < 30 secondes via un reload Nginx (connexions en cours préservées en mode graceful)
- **Risque dilué** : un bug sur la Phase 2 n'impacte que le commerce, pas les RDVs ou l'auth
- **Parallélisme** : l'équipe peut continuer à livrer des features produit sur Laravel pendant la migration Python

### Négatives
- **Maintenance duale** : pendant les phases 0-4, les deux backends doivent être opérationnels
- **Synchronisation de schéma** : toute migration Alembic doit rester compatible avec le schéma Laravel (éviter les renommages de colonnes pendant la transition)
- **Complexité Nginx** : la config dual-stack `staging.conf` doit être maintenue à jour avec chaque phase
- **Durée totale** : 16-17 semaines vs 4-6 semaines pour un big bang (mais avec un risque incomparablement plus faible)

### Contraintes techniques durant la transition
- Les migrations de base de données doivent être **rétrocompatibles** (jamais supprimer une colonne utilisée par Laravel)
- Les formats de tokens JWT doivent être compatibles entre les deux backends (même secret, même algorithme)
- Les uploads de fichiers sont partagés via un volume commun (S3 ou NFS) accessible aux deux backends
