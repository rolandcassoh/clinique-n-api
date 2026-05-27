from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class CurrencySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    symbol: str
    exchange_rate: Decimal
    is_default: bool


class CurrencyCreateSchema(BaseModel):
    name: str
    code: str
    symbol: str
    exchange_rate: Decimal = Decimal("1")
    is_default: bool = False
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def code_uppercase(cls, v: str) -> str:
        return v.upper()


class CurrencyUpdateSchema(BaseModel):
    name: str
    code: str
    symbol: str
    exchange_rate: Decimal
    is_default: bool = False
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def code_uppercase(cls, v: str) -> str:
        return v.upper()
