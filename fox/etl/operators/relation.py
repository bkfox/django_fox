from typing import NamedTuple

from ..record_set import Lookup
from .base import Operator

__all__ = ("RelationBound", "Relation")


class RelationBound(NamedTuple):
    def __init__(self, relation, index):
        self.relation = relation
        self.index = index


class Relation(Operator):
    """Relation to one model."""

    def __init__(self, set_name, lookup=None):
        self.set_name = set_name
        self.lookup = lookup and Lookup(lookup)

    def call(self, value):
        return RelationBound(self, value)

    def resolve(self, pool, index):
        """Resolve relation using provided pool and element index.

        Return None if not found.
        """
        record_set = pool.get(self.set_name)
        if record_set is None:
            return None
        return record_set.get(index, lookup=self.lookup)

    def resolve_many(self, pool, indexes):
        """Resolve many indexes at once, returning None or all of found
        ones."""
        record_set = pool.get(self.set_name)
        if record_set is None:
            return None
        return record_set.get_many(indexes, lookup=self.lookup)
