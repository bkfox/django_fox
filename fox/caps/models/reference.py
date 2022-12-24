from __future__ import annotations
from collections.abc import Iterable

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .agent import Agent
from .capability import Capability
from .capability_set import BaseCapabilitySet


__all__ = ('ReferenceQuerySet', 'Reference',)


class ReferenceQuerySet(models.QuerySet):
    """ QuerySet for Reference classes. """

    class Meta:
        abstract = True
        unique_together = (('receiver', 'target', 'emitter'),)

    def emitter(self, agents: Agent) -> ReferenceQuerySet:
        """
        References for the provided Agent emitter
        :param Agent agents: single Agent.
        """
        return self.filter(origin__receiver=agents)

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

    def bulk_create(self, objs, *a, **kw):
        for obj in objs:
            obj.is_valid()
        return super().bulk_create(objs, *a, **kw)

    # TODO: bulk_update -> is_valid()


class Reference(BaseCapabilitySet, models.Model):
    """
    Reference are set of capabilities targeting a specific object.
    There are two kind of reference:
        - root: the root reference from which all other references to object
                are derived. Created from the `create()` class method.
        - derived: reference derived from root or another derived. Created
                from the `derive()` class method.

    This class enforce fields validation at `save()` and `bulk_create()`.

    This model is implemented as an abstract in order to have a reference
    specific to each model (see `Object` abstract model).

    """
    ref = models.UUIDField(_('Public Reference'), default=uuid.uuid4,
                           db_index=True)
    """ Public reference used in API and with the external world """
    origin = models.ForeignKey('self', models.CASCADE, blank=True, null=True,
                               verbose_name=_('Source Reference'))
    """ Source reference in references chain. """
    depth = models.PositiveIntegerField(_('Share Count'), default=0)
    """ Reference chain's current depth. """
    receiver = models.ForeignKey(Agent, models.CASCADE,)
    """ Agent receiving capability. """
    target = models.ForeignKey('ConcreteObject', models.CASCADE)
    """ Reference's target. """
    capabilities = models.ManyToManyField(Capability,
                                          verbose_name=_('Capability'))

    objects = ReferenceQuerySet.as_manager()

    class Meta:
        abstract = True
        unique_together = (('origin', 'receiver', 'target'),)

    @property
    def emitter(self):
        """ Agent emitting the reference. """
        return self.origin.receiver if self.origin else self.receiver

    def is_valid(self) -> bool:
        """
        Check Reference values validity, throwing exception on invalid values.
        :returns True if valid, otherwise raise ValueError
        """
        if self.origin:
            # if self.origin.receiver != self.emitter:
            #    raise ValueError("origin's receiver and self's emitter are "
            #                     "different")
            if self.origin.depth >= self.depth:
                raise ValueError("origin's depth is higher than self's")
        return True

    @classmethod
    def create(cls, emitter: Agent, target: object,
               capabilities: Iterable[Capability], **kw) -> Reference:
        """
        Create and save a new root reference with provided
        capabilities.
        """
        if 'origin' in kw:
            raise ValueError(
                'attribute "origin" can not be passed as an argument to '
                '`create()`: you should use derive instead')

        self = cls(receiver=emitter, target=target, **kw)
        self.save()
        self.capabilities.add(*capabilities)
        return self

    def is_derived(self, other: Reference) -> bool:
        if other.depth <= self.depth or self.target != other.target:
            return False
        return super().is_derived(other)

    def get_capabilities(self):
        return self.capabilities.all()

    def derive(self, receiver: Agent,
               items: BaseCapabilitySet.DeriveItems = None,
               update: bool = False) -> Reference:
        """
        Derive this `CapabilitySet` from `self`.

        :param Agent receiver: receiver of the new reference
        :param DeriveItems items: if provided, only derive those capabilities
        :param bool update: update existing reference if it exists
        """
        subset = None
        if update:
            queryset = self.objects.filter(origin=self, receiver=receiver,
                                           target=self.target)
            subset = queryset.first()

        capabilities = self.derive_caps(items)
        if subset is None:
            subset = type(self)(origin=self, depth=self.depth+1,
                                receiver=receiver, target=self.target)
        subset.save()
        subset.capabilities.add(*capabilities)
        return subset

    def save(self, *a, **kw):
        self.is_valid()
        return super().save(*a, **kw)
