from __future__ import annotations
from collections.abc import Iterable
from typing import Union

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


from .agent import Agent
from .capability import Capability
from .capability_set import BaseCapabilitySet


__all__ = ('ReferenceQuerySet', 'Reference',)


class ReferenceQuerySet(models.QuerySet):
    Agents: Union[Agent, Iterable[Agent]]

    def subsets(self, reference: Reference) -> ReferenceQuerySet:
        """ Return references shared from provided one. """
        return self.filter(origin=reference)

    def emitter(self, agents: Agents) -> ReferenceQuerySet:
        """
        References for the provided Agent emitter
        :param Agent agents: single Agent or iterable of Agents .
        """
        if isinstance(agents, self.model):
            return self.filter(emitter=agents)
        return self.filter(emitter__in=agents)

    def receiver(self, agents: Agents) -> ReferenceQuerySet:
        """
        References for the provided Agent receiver
        :param Agent agents: single Agent or iterable of Agents .
        """
        if isinstance(agents, self.model):
            return self.filter(receiver=agents)
        return self.filter(receiver__in=agents)

    def ref(self, receiver: Agents, ref: uuid.UUID) -> ReferenceQuerySet:
        """ References for the external ref. """
        return self.filter(ref=ref).receiver(receiver)


class Reference(BaseCapabilitySet):
    """
    Holds a reference to an object with capabilities.

    A Reference must always be fetched with a requerring Agent.
    """
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

    target_id = models.PositiveIntegerField(_('Target ID'), db_index=True)
    """ Target object id. """
    target_model = models.ForeignKey(ContentType, models.CASCADE,
                                     verbose_name=_('Target Model'))
    """ Target object model. """
    target = GenericForeignKey('target_model', 'target_id')
    """ Target. """

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
