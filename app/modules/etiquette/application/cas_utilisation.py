"""Cas d'utilisation du module tag."""
from app.modules.etiquette.domain.entites import Tag
from app.modules.etiquette.domain.exceptions import TagNotFoundError, TagSlugConflictError
from app.modules.etiquette.domain.depots import AbstractTagRepository


class TagUseCases:
    def __init__(self, repo: AbstractTagRepository) -> None:
        self._repo = repo

    async def list_tags(self, type_filter: str | None = None, search: str | None = None) -> list[Tag]:
        return await self._repo.list(type_filter=type_filter, search=search)

    async def get_tag(self, tag_id: int) -> Tag:
        etiquette = await self._repo.get_by_id(tag_id)
        if etiquette is None:
            raise TagNotFoundError(tag_id)
        return etiquette

    async def create_tag(self, nom: str, identifiant_url: str, type: str | None) -> Tag:
        existant = await self._repo.get_by_slug(identifiant_url)
        if existant is not None:
            raise TagSlugConflictError(identifiant_url)
        return await self._repo.create(nom=nom, identifiant_url=identifiant_url, type=type)

    async def update_tag(self, tag_id: int, nom: str, identifiant_url: str, type: str | None) -> Tag:
        # Vérifier le conflit de identifiant_url sur une autre étiquette
        existant = await self._repo.get_by_slug(identifiant_url)
        if existant is not None and existant.id != tag_id:
            raise TagSlugConflictError(identifiant_url)
        mis_a_jour = await self._repo.update(tag_id, nom=nom, identifiant_url=identifiant_url, type=type)
        if mis_a_jour is None:
            raise TagNotFoundError(tag_id)
        return mis_a_jour

    async def delete_tag(self, tag_id: int) -> None:
        supprime = await self._repo.soft_delete(tag_id)
        if not supprime:
            raise TagNotFoundError(tag_id)
