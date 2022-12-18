from __future__ import annotations
from collections.abc import Iterable
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


from .agent import Agent
from .reference import Reference

# Problem: we need to fetch reference at the same time as object.
# Possible solution:
# - create a Reference subclass targeting object which can then be prefetech
#   from reference. 
# - prefetch somehow from object reference, but complicate du to how GenericForeignKey
#   works.


class ObjectBase(models.ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        reference_class = attrs.get('Reference')
        new_class = super(ObjectBase, cls).__new__(name, bases, attrs, **kwargs)
        if reference_class:
            return new_class

        reference_class = type(name + 'Ref', [Reference], {
            'target': models.ForeignKey(
                new_class, models.CASCADE, db_index=True,
                related_name='reference_set',
                verbose_name=_('Target'),
            )
        })
        setattr(new_class, 'Reference', reference_class)
        return new_class


class ObjectQuerySet(models.QuerySet):
    def ref(self, receiver: Agent, ref: uuid.UUID):
        """ Return reference for provided receiver and ref. """
        return self.model.Reference.objects.ref(receiver, ref)

    def refs(self, receiver: Agent, ref: Iterable[uuid.UUID]):
        """ Return references for provided receiver and refs. """
        return self.model.Reference.objects.refs(receiver, ref)


class Object(models.Model, metaclass=ObjectBase):
    class Meta:
        abstract = True

