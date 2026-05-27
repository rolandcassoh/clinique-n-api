"""Exceptions métier du module RequestService."""
from app.shared.exceptions.domain import ConflictError, EntityNotFoundError


class RequestServiceNotFoundError(EntityNotFoundError):
    def __init__(self, request_id: int) -> None:
        super().__init__("RequestService", request_id)


class RequestServiceCannotCancelError(ConflictError):
    def __init__(self, request_id: int, status: str) -> None:
        super().__init__(
            f"RequestService {request_id} cannot be cancelled (status='{status}'). "
            "Only 'pending' requests can be cancelled."
        )


class RequestServiceAccessDeniedError(ConflictError):
    def __init__(self, request_id: int) -> None:
        super().__init__(f"Access denied to RequestService {request_id}.")
