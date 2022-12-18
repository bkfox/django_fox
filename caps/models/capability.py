from __future__ import annotations
from typing import Union
from collections.abc import Iterable

from asgiref.sync import sync_to_async
import functools
import operator

from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.db.models import Q
from django.utils.translation import gettext_lazy as _, gettext as __


__all__ = ('CapabilityQuerySet', 'Capability')


class CapabilityQuerySet(models.QuerySet):
    def _get_items_queryset(self, items) -> models.QuerySet:
        """ Get or create capabilities from database. """
        q_objects = (Q(name=r.name, max_derive=r.max_derive) for r in items)
        query = functools.reduce(operator.or_, q_objects)
        return self.filter(query)

    def get_or_create_many(self, items: Iterable[Capability]) \
            -> models.Queryset:
        """
        Retrieve capabilities from database, create it if missing. Subset's
        items are updated.
        """
        queryset = self._get_items_queryset(items)
        # force queryset to use a different cache, in order to return it
        # unevaluated
        names = {r.name for r in queryset.all()}
        missing = (item for item in items if item.name not in names)
        with transaction.atomic(queryset.db):
            Capability.objects.bulk_create(missing)
        return queryset

    # FIXME: awaits for django.transaction async support
    async def aget_or_create_many(self, items: Iterable[Capability]) \
            -> models.Queryset:
        """ Async version of `get_or_create_many`. """
        func = sync_to_async(self.get_or_create_many)
        return await func(items)


class Capability(models.Model):
    """
    A single capability. Provide permission for a specific action.
    Capability are stored as unique for each action/max_derive couple.
    """
    IntoValue: Union[tuple[str, str], list[str], Capability]

    name = models.CharField(_('Action'), max_length=32, db_index=True)
    max_derive = models.PositiveIntegerField(
        _('Maximum Derivation'), default=0)

    objects = CapabilityQuerySet.as_manager()

    @classmethod
    def into(cls, value: IntoValue):
        """
        Return a Capability based on value.

        Value formats: `(name, max_derive)`, `{name: _, max_derive: _}`,
        `Capability` (returned as is in this case)
        """
        if isinstance(value, (list, tuple)):
            return cls(name=value[0], max_derive=value[1])
        if isinstance(value, dict):
            return cls(**value)
        if isinstance(value, Capability):
            return value
        raise NotImplementedError('Provided values are not supported')

    def can_derive(self, max_derive: Union[None, int] = None) -> bool:
        """ Return True if this capability can be derived. """
        return self.max_derive > 0 and \
            (max_derive is None or max_derive < self.max_derive)

    def derive(self, max_derive: Union[None, int] = None) -> Capability:
        """
        Derive a new capability from self (without checking existence in
        database).
        """
        if not self.can_derive(max_derive):
            raise PermissionDenied(__('can not derive capability {name}')
                                   .format(name=self.name))
        if max_derive is None:
            max_derive = self.max_derive-1
        return Capability(name=self.name, max_derive=max_derive)

    def is_derived(self, capability: Capability = None) -> bool:
        """
        Return True if `capability` is derived from this one.
        """
        return self.name == capability.name and \
            self.can_derive(capability.max_derive)

    def __contains__(self, other: Capability):
        """
        Return True if other `capability` is derived from `self`.
        """
        return self.is_derived(other)

    def __eq__(self, other: Capability):
        if self.pk and other.pk:
            return self.pk == other.pk
        return self.name == other.name and self.max_derive == other.max_derive

    class Meta:
        unique_together = ('name', 'max_derive')
