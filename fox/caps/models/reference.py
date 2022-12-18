from __future__ import annotations
from collections.abc import Iterable
from typing import Union

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


from .agent import Agent
from .capability import Capability
from .capability_set import BaseCapabilitySet


__all__ = ('ReferenceQuerySet', 'Reference',)


class ReferenceQuerySet(models.QuerySet):
    # TODO: remove
    Agents: Union[Agent, Iterable[Agent]]

    def subsets(self, reference: Reference) -> ReferenceQuerySet:
        """ Return references shared from provided one. """
        return self.filter(origin=reference)

    def emitter(self, agents: Agent) -> ReferenceQuerySet:
        """
        References for the provided Agent emitter
        :param Agent agents: single Agent.
        """
        return self.filter(emitter=agents)

    def receiver(self, agents: Agent) -> ReferenceQuerySet:
        """
        References for the provided Agent receiver
        :param Agent agents: single Agent.
        """
        return self.filter(receiver=agents)

    def ref(self, receiver: Agent, ref: uuid.UUID) -> ReferenceQuerySet:
        """ Reference by ref and receiver. """
        return self.receiver(receiver).get(ref=ref)

    def refs(self, receiver: Agent, refs: Iterable[uuid.UUID]) \
            -> ReferenceQuerySet:
        """ References by ref and receiver. """
        return self.receiver(receiver).filter(ref__in=refs)


class Reference(BaseCapabilitySet, models.Model):
    """
    Holds a reference to an object with capabilities.

    A Reference must always be fetched with a requerring Agent.
    """
    # FIXME: enforce:
    # - that all Reference on platform inherits from a single `origin`
    #   root object. It may also be interesting to allow extending
    #   existing references' capabilities recursively.
    # - emitter to always be the same as origin's
    #   potentially: RelatedField that fetch value from related object
    #   as in Odoo
    # - check capabilities origins
    ref = models.UUIDField(_('Public Reference'), default=uuid.uuid4,
                           db_index=True)
    """ Public reference used in API and with the external world """
    origin = models.ForeignKey('self', models.CASCADE, blank=True, null=True,
                               verbose_name=_('Source Reference'))
    """ Source reference in references chain. """
    depth = models.PositiveIntegerField(_('Share Count'), default=0)
    """ Reference chain's current depth. """
    emitter = models.ForeignKey(Agent, models.CASCADE,
                                verbose_name=_('Emitter'))
    """ Agent emitting the reference. """
    receiver = models.ForeignKey(Agent, models.CASCADE,)
    """ Agent receiving capability. """
    target = models.ForeignKey('ConcreteObject', models.CASCADE)
    """ Reference's target. """

    class Meta:
        abstract = True
        unique_together = (('receiver', 'target', 'emitter'),)

    def is_derived(self, other: Reference) -> bool:
        if other.depth < self.depth or self.target != other.target:
            return False
        return super().is_derived(other)

    def derive(self, receiver: Agent, items: BaseCapabilitySet.DeriveItems) \
            -> Reference:
        """
        Derive this `CapabilitySet` from `self`.
        """
        capabilities = self.derive_caps(items)
        capabilities = Capability.objects.bulk_create(capabilities)
        subset = type(self)(capabilities, origin=self, depth=self.depth+1,
                            emitter=self.receiver, receiver=receiver,
                            target=self.target)
        subset.save()
        subset.capabilities.add(**capabilities)
        return super().derive(items, )
