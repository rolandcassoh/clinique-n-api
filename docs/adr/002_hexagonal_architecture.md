# ADR-002 : Architecture Hexagonale (Ports & Adapters)

**Statut** : Accepté  
**Date** : 2025-01-22  
**Auteur** : Lead Architecture  
**Réviseurs** : Équipe Backend

---

## Contexte

En migrant vers FastAPI, il était tentant de reproduire le pattern Laravel (ActiveRecord + Controllers épais). L'expérience avec le monolithe Laravel a montré les limites de cette approche :

- Les tests nécessitent une base de données réelle (couplage fort avec Eloquent)
- La logique métier est dispersée dans les Controllers, Repositories, Traits et Events
- Remplacer un composant externe (ex : passer de MySQL à PostgreSQL, de Stripe à un autre PSP) nécessite de modifier plusieurs couches
- Les règles métier ne peuvent pas être testées sans bootstrapper le framework

Le projet adopte donc l'**architecture hexagonale** (Ports & Adapters, Alistair Cockburn, 2005).

## Décision

Organiser le code en quatre couches strictement séparées, les dépendances ne pouvant pointer que vers l'intérieur.

### Structure des couches

```
app/
├── domain/              # Couche 1 : Domaine (aucune dépendance externe)
│   ├── entities/        # Entités et Value Objects
│   ├── repositories/    # Interfaces (ports) des repositories
│   ├── services/        # Services de domaine
│   └── exceptions/      # Exceptions métier
│
├── application/         # Couche 2 : Application (orchestre le domaine)
│   ├── use_cases/       # Un fichier = un cas d'usage
│   ├── dtos/            # Data Transfer Objects (entrée/sortie)
│   └── ports/           # Interfaces des services externes
│
├── infrastructure/      # Couche 3 : Adapters secondaires (driven)
│   ├── persistence/     # Implémentations SQLAlchemy des repositories
│   ├── email/           # Adapter SMTP / SendGrid
│   ├── payment/         # Adapter Stripe / PayPal
│   ├── storage/         # Adapter S3 / local filesystem
│   └── cache/           # Adapter Redis
│
└── api/                 # Couche 4 : Adapters primaires (driving)
    ├── routers/         # Routes FastAPI par module
    ├── schemas/         # Schémas Pydantic (request/response)
    └── dependencies/    # Injection de dépendances FastAPI
```

### Règle de dépendance

```
api → application → domain
infrastructure → application → domain
```

Le domaine ne connaît ni FastAPI, ni SQLAlchemy, ni aucune librairie externe.

### Exemple concret : création d'un RDV

```python
# domain/repositories/appointment_repository.py (interface = port)
class AppointmentRepository(Protocol):
    async def save(self, appointment: Appointment) -> Appointment: ...
    async def find_by_id(self, id: UUID) -> Appointment | None: ...

# application/use_cases/create_appointment.py
class CreateAppointmentUseCase:
    def __init__(self, repo: AppointmentRepository, notifier: NotificationPort):
        self._repo = repo
        self._notifier = notifier

    async def execute(self, dto: CreateAppointmentDTO) -> AppointmentDTO:
        appointment = Appointment.create(dto.doctor_id, dto.patient_id, dto.slot)
        saved = await self._repo.save(appointment)
        await self._notifier.send_confirmation(saved)
        return AppointmentDTO.from_entity(saved)

# infrastructure/persistence/sqlalchemy_appointment_repo.py (adapter)
class SQLAlchemyAppointmentRepository:
    async def save(self, appointment: Appointment) -> Appointment:
        model = AppointmentModel.from_entity(appointment)
        self.session.add(model)
        await self.session.flush()
        return model.to_entity()

# api/routers/appointments.py (adapter primaire)
@router.post("/appointments")
async def create_appointment(
    dto: CreateAppointmentRequest,
    use_case: CreateAppointmentUseCase = Depends(get_create_appointment_use_case),
) -> AppointmentResponse:
    return await use_case.execute(dto)
```

## Alternatives considérées

### Architecture en couches classiques (MVC)
- **Pour** : familière, moins de fichiers, moins d'abstractions
- **Contre** : couplage fort, tests difficiles, impossible de remplacer SQLAlchemy ou Stripe sans toucher la logique métier

### CQRS + Event Sourcing
- **Pour** : séparation lecture/écriture optimale, audit trail complet
- **Contre** : complexité excessive pour le niveau actuel, eventstore à maintenir, équipe non formée

### Clean Architecture (Robert Martin)
- **Pour** : très proche de l'hexagonale, bien documentée
- **Contre** : plus de couches (Entities, Use Cases, Interface Adapters, Frameworks), overhead pour une API REST

## Conséquences

### Positives
- **Testabilité** : le domaine et les use cases sont testables avec des mocks en mémoire, sans base de données
- **Remplacement d'adapters** : changer de PSP (Stripe → PayPal) = écrire un nouvel adapter sans toucher les use cases
- **Lisibilité** : un use case = un fichier = une responsabilité claire
- **Isolation du domaine** : les règles métier (règles de RDV, calcul commissions) ne peuvent pas être polluées par des détails techniques
- **Onboarding** : un nouveau développeur trouve immédiatement où est la logique métier

### Négatives
- **Verbosité** : plus de fichiers et d'interfaces qu'une architecture MVC classique
- **Courbe d'apprentissage** : les développeurs habitués à ActiveRecord doivent changer de paradigme
- **Sur-ingénierie possible** : pour des modules simples (CRUD pur), les couches ajoutent de la friction

### Règle pragmatique adoptée
Pour les modules purement CRUD sans logique métier (ex : `countries`, `currencies`, `tags`), une architecture simplifiée directe Router → Repository → SQLAlchemy est acceptée. L'hexagonale complète est réservée aux modules avec des règles métier (appointments, billing, commissions).
