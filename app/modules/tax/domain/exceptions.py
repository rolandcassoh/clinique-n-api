from app.shared.exceptions.domain import DomainException


class TaxNotFoundError(DomainException):
    def __init__(self, tax_id: int) -> None:
        super().__init__(f"Tax with id '{tax_id}' not found.")
        self.tax_id = tax_id


class NoDefaultTaxError(DomainException):
    def __init__(self) -> None:
        super().__init__("No default tax configured.")
