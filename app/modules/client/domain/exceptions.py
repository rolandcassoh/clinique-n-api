from app.shared.exceptions.domain import DomainException


class FamilyMemberNotFoundError(DomainException):
    def __init__(self, member_id: int) -> None:
        super().__init__(f"Membre de famille avec l'identifiant '{member_id}' introuvable.")
        self.member_id = member_id


class FamilyMemberAccessDeniedError(DomainException):
    def __init__(self, member_id: int) -> None:
        super().__init__(f"Accès refusé au membre de famille '{member_id}'.")
        self.member_id = member_id


class CustomerProfileNotFoundError(DomainException):
    def __init__(self, id_utilisateur: int) -> None:
        super().__init__(f"Profil client pour l'utilisateur '{id_utilisateur}' introuvable.")
        self.id_utilisateur = id_utilisateur
