from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class InMemoryRepository(Generic[T]):
    def __init__(self) -> None:
        self._store: dict[UUID, T] = {}

    def save(self, entity: T) -> T:
        self._store[entity.id] = entity  # type: ignore[attr-defined]
        return entity

    def get(self, id: UUID) -> T | None:
        return self._store.get(id)

    def list_all(self) -> list[T]:
        return list(self._store.values())

    def list_by(self, **filters) -> list[T]:
        results = list(self._store.values())
        for key, value in filters.items():
            results = [r for r in results if getattr(r, key, None) == value]
        return results

    def delete(self, id: UUID) -> bool:
        if id in self._store:
            del self._store[id]
            return True
        return False

    def exists(self, id: UUID) -> bool:
        return id in self._store

    def find_one(self, **filters) -> T | None:
        matches = self.list_by(**filters)
        return matches[0] if matches else None
