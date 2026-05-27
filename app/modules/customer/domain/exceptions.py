from app.shared.exceptions.domain import DomainException


class FamilyMemberNotFoundError(DomainException):
    def __init__(self, member_id: int) -> None:
        super().__init__(f"Family member with id '{member_id}' not found.")
        self.member_id = member_id


class FamilyMemberAccessDeniedError(DomainException):
    def __init__(self, member_id: int) -> None:
        super().__init__(f"Access denied to family member '{member_id}'.")
        self.member_id = member_id


class CustomerProfileNotFoundError(DomainException):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"Customer profile for user '{user_id}' not found.")
        self.user_id = user_id
