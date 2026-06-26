"""Exceptions métier du module RequestService."""
from app.shared.exceptions.domain import ConflictError, EntityNotFoundError


class RequestServiceNotFoundError(EntityNotFoundError):
    def __init__(self, request_id: int) -> None:
        super().__init__("RequestService", request_id)


class RequestServiceCannotCancelError(ConflictError):
    def __init__(self, request_id: int, statut: str) -> None:
        super().__init__(
            f"La demande de service {request_id} ne peut pas être annulée (statut='{statut}'). "
            "Seules les demandes en statut 'pending' peuvent être annulées."
        )


class RequestServiceAccessDeniedError(ConflictError):
    def __init__(self, request_id: int) -> None:
        super().__init__(f"Accès refusé à la demande de service {request_id}.")
