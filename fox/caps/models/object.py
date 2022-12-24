from __future__ import annotations
from collections.abc import Iterable
from uuid import UUID

from django.db import models
from django.db.models import OuterRef, Subquery
from django.utils.translation import gettext_lazy as _


from .agent import Agent
from .reference import Reference


__all__ = ('ObjectBase', 'ObjectQuerySet', 'Object')


class ObjectBase(models.base.ModelBase):
    """
    Metaclass for Object model classes.
    It subclass Reference if no `Reference` member is provided.
    """

    @classmethod
    def get_reference_class(cls, name, bases, attrs):
        """
        Return the reference class to self
        """
        reference_class = attrs.get('Reference')
        if not reference_class:
            bases = (b for b in bases if hasattr(b, '_meta') and not b._meta.abstract)
            items = (r for r in (getattr(b, 'Reference', None) for b in bases)
                     if isinstance(r, Reference))
            reference_class = next(items, None)
        elif not issubclass(reference_class, Reference):
            raise ValueError("{} Reference member must be a subclass "
                             "of `fox.caps.models.Reference`"
                             .format(name))
        return reference_class
    
    def __new__(cls, name, bases, attrs, **kwargs):
        # FIXME: models inherited from concrete model should check
        # on parent model's existing member `Reference`.
        reference_class = cls.get_reference_class(name, bases, attrs)
        new_class = super(ObjectBase, cls).__new__(cls, name, bases, attrs, **kwargs)
        if new_class._meta.abstract:
            return new_class

        if reference_class:
            if not issubclass(reference_class, Reference):
                raise ValueError("Model's Reference member must be a subclass "
                                 "of `fox.caps.models.Reference`")
            return new_class

        reference_class = type(name + 'Reference', (Reference,), {
            'target': models.ForeignKey(
                new_class, models.CASCADE, db_index=True,
                related_name='reference_set',
                verbose_name=_('Target'),
            ),
            '__module__': new_class.__module__,
        })
        setattr(new_class, 'Reference', reference_class)
        return new_class


class ObjectQuerySet(models.QuerySet):
    """ QuerySet for Objects. """

    # TODO: ref and refs should return Object instance annotated with
    # the actual reference.
    # this allows using object's queryset values
    def ref(self, receiver: Agent, ref: UUID):
        """ Return reference for provided receiver and ref. """
        subquery = self.model.Reference.objects.filter(target=OuterRef('pk')) \
                                               .ref(receiver, ref)
        return self.filter(reference=Subquery(subquery)[:1])

    def refs(self, receiver: Agent, ref: Iterable[UUID]):
        """ Return references for provided receiver and refs. """
        subquery = self.model.Reference.objects.filter(target=OuterRef('pk')) \
                                               .refs(receiver, ref)
        return self.filter(reference=Subquery(subquery)[:1])


class Object(models.Model, metaclass=ObjectBase):
    """
    An object accessible through References.

    It can have a member `Reference` (subclass of `fox.caps.models.Reference`)
    that is used as object's specific reference. If none is provided, a
    it will be generated automatically for concrete classes.
    """
    objects = ObjectQuerySet.as_manager()

    class Meta:
        abstract = True

    # def get_reference(self, receiver: Agent) -> Reference:
