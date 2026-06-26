from typing import Any, Generic, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class CRUDRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, record_id: int) -> ModelT | None:
        resultat = await self.session.get(self.model, record_id)
        if resultat and resultat.is_deleted:
            return None
        return resultat

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
        include_deleted: bool = False,
    ) -> tuple[list[ModelT], int]:
        requete = select(self.model)
        requete_comptage = select(func.count()).select_from(self.model)

        if not include_deleted:
            requete = requete.where(self.model.deleted_at.is_(None))
            requete_comptage = requete_comptage.where(self.model.deleted_at.is_(None))

        if filters:
            for colonne, valeur in filters.items():
                requete = requete.where(getattr(self.model, colonne) == valeur)
                requete_comptage = requete_comptage.where(getattr(self.model, colonne) == valeur)

        resultat_total = await self.session.execute(requete_comptage)
        total = resultat_total.scalar_one()

        requete = requete.offset(offset).limit(limit)
        resultat = await self.session.execute(requete)
        lignes = list(resultat.scalars().all())

        return lignes, total

    async def create(self, **data: Any) -> ModelT:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, record_id: int, **data: Any) -> ModelT | None:
        instance = await self.get_by_id(record_id)
        if instance is None:
            return None
        for cle, valeur in data.items():
            setattr(instance, cle, valeur)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def soft_delete(self, record_id: int) -> bool:
        instance = await self.get_by_id(record_id)
        if instance is None:
            return False
        instance.soft_delete()
        await self.session.flush()
        return True

    async def hard_delete(self, record_id: int) -> bool:
        instance = await self.session.get(self.model, record_id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
