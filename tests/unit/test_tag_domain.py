"""Tests unitaires — domaine Tag (logique pure, sans I/O)."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.modules.etiquette.application.cas_utilisation import TagUseCases
from app.modules.etiquette.domain.entites import Tag
from app.modules.etiquette.domain.exceptions import TagNotFoundError, TagSlugConflictError


def _make_tag(id: int = 1, slug: str = "news") -> Tag:
    return Tag(id=id, name="News", slug=slug, type="blog", created_at=datetime.now(timezone.utc))


class TestTagUseCases:
    def _repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_tag_raises_not_found_when_missing(self) -> None:
        repo = self._repo()
        repo.get_by_id.return_value = None
        uc = TagUseCases(repo)

        with pytest.raises(TagNotFoundError):
            await uc.get_tag(99)

    @pytest.mark.asyncio
    async def test_create_raises_conflict_on_duplicate_slug(self) -> None:
        repo = self._repo()
        repo.get_by_slug.return_value = _make_tag(slug="already-taken")
        uc = TagUseCases(repo)

        with pytest.raises(TagSlugConflictError):
            await uc.create_tag(name="Autre", slug="already-taken", type=None)

    @pytest.mark.asyncio
    async def test_create_succeeds_with_unique_slug(self) -> None:
        repo = self._repo()
        repo.get_by_slug.return_value = None
        created = _make_tag(slug="unique-slug")
        repo.create.return_value = created
        uc = TagUseCases(repo)

        result = await uc.create_tag(name="Unique", slug="unique-slug", type="blog")

        repo.create.assert_awaited_once_with(name="Unique", slug="unique-slug", type="blog")
        assert result.slug == "unique-slug"

    @pytest.mark.asyncio
    async def test_update_raises_conflict_when_slug_taken_by_other(self) -> None:
        repo = self._repo()
        # Slug pris par un tag différent (id=2)
        repo.get_by_slug.return_value = _make_tag(id=2, slug="taken")
        uc = TagUseCases(repo)

        with pytest.raises(TagSlugConflictError):
            await uc.update_tag(tag_id=1, name="X", slug="taken", type=None)

    @pytest.mark.asyncio
    async def test_update_allows_same_slug_on_same_tag(self) -> None:
        repo = self._repo()
        tag = _make_tag(id=1, slug="my-slug")
        repo.get_by_slug.return_value = tag
        repo.update.return_value = tag
        uc = TagUseCases(repo)

        result = await uc.update_tag(tag_id=1, name="Updated", slug="my-slug", type=None)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_delete_raises_not_found_when_missing(self) -> None:
        repo = self._repo()
        repo.soft_delete.return_value = False
        uc = TagUseCases(repo)

        with pytest.raises(TagNotFoundError):
            await uc.delete_tag(42)

    @pytest.mark.asyncio
    async def test_list_delegates_to_repo(self) -> None:
        repo = self._repo()
        repo.list.return_value = [_make_tag()]
        uc = TagUseCases(repo)

        result = await uc.list_tags(type_filter="blog", search="ne")

        repo.list.assert_awaited_once_with(type_filter="blog", search="ne")
        assert len(result) == 1
