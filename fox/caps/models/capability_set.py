from __future__ import annotations
from collections.abc import Iterable
from typing import Union

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as __

from .capability import Capability


__all__ = ('BaseCapabilitySet', 'CapabilitySet')


class BaseCapabilitySet:
    """ Handle a set of capabilities. """
    DeriveItems: Iterable[Union[str, Capability.IntoValue]]
    capabilities = None

    def is_derived(self, other: CapabilitySet) -> bool:
        """
        Return True if `capabilities` iterable is a subset of self.

        Set is a subset of another one if and only if:
        - all capabilities of subset are in set and derived from set \
          (cf. `Capability.is_subset`)
        - there is no capability inside subset that are not in set.
        """
        items = other.capabilities
        capabilities = {c.name: c for c in self.capabilities}
        for item in items:
            capability = capabilities.get(item.name)
            if not capability or not capability.is_derived(item):
                return False
        return True

    def derive_caps(self, items: DeriveItems = None) -> list[Capability]:
        """
        Derive all capabilities from this set using provided optionnal
        iterator.
        :return an array of Capability instances (may not all be saved).
        """
        if items is None:
            return [Capability(name=r.name, max_derive=0)
                    for r in self.capabilities]
        return self._derive_caps(self.capabilities, items)

    async def aderive_caps(self, items: DeriveItems = None) -> list[Capability]:
        """
        Async version of `derive_caps`.
        """
        if items is None:
            return [Capability(name=r.name, max_derive=0)
                    async for r in self.capabilities]
        return self._derive_caps((r async for r in self.capabilities), items)

    def _derive_caps(self, source: Iterable[Capability],
                     items: DeriveItems) -> list[Capability]:
        """ Derive capabilities using given dict of parents """
        by_name = {r.name: r for r in source}
        derived, denied = [], []
        for item in items:
            item = Capability.into(item)
            capability = by_name.get(item.name)
            if capability and item.max_derive is None:
                item.max_derive = capability.max_derive-1
            if not capability or not capability.is_derived(item):
                denied.append(item.name)
            else:
                derived.append(item)

        if denied:
            raise PermissionDenied(
                __('Some capabilities can not be derived: {denied}')
                .format(denied=', '.join(denied)))
        return derived


class CapabilitySet(BaseCapabilitySet):
    def __init__(self, capabilities: Iterable[Capability]):
        self.capabilities = list(capabilities)

    def derive(self, items: Capability.DeriveItems = None, **init_kwargs) \
            -> CapabilitySet:
        """
        Derive this `CapabilitySet` from `self`.
        """
        capabilities = self.derive_caps(items)
        capabilities = Capability.objects.bulk_create_many(capabilities)
        return type(self)(capabilities, **init_kwargs)
