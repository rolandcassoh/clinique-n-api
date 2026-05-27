# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project scaffold with FastAPI + SQLAlchemy 2.0 async
- Hexagonal architecture: domain / application / infrastructure / api layers
- Auth module: register, login, JWT refresh, logout, 2FA TOTP, OTP email
- Shared: BaseModel with timestamps + soft delete, CRUDRepository, Page[T] pagination
- Core: JWT handler, bcrypt passwords, Redis cache, structured logging, security headers
- Storage port (LocalStorageAdapter for dev), NotificationPort, PaymentPort ABCs
- Docker Compose stack: api, celery, mysql 8.0, redis 7, meilisearch, mailhog
- Alembic migrations setup
- Test suite: async SQLite fixtures, UserFactory, domain unit tests
