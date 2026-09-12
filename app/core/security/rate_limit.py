"""Limitation de débit (rate limiting) basée sur Redis via slowapi.

Utilisé pour protéger les points d'entrée d'authentification contre les
attaques par force brute (connexion, inscription, réinitialisation de mot
de passe).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# Le stockage Redis est partagé avec le reste de l'application (voir
# app/core/cache/redis_client.py) — slowapi gère sa propre connexion via
# l'URI de stockage.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    strategy="fixed-window",
    # headers_enabled nécessite que chaque endpoint décoré déclare un
    # paramètre `response: Response` (slowapi injecte les en-têtes
    # X-RateLimit-* dessus) — nos endpoints renvoient des modèles Pydantic,
    # pas des Response, donc on désactive l'injection d'en-têtes.
    headers_enabled=False,
)
