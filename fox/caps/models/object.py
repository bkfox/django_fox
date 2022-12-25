from __future__ import annotations
from collections.abc import Iterable
from uuid import UUID

from django.db import models
from django.db.models import OuterRef, Prefetch, Subquery
from django.utils.functional import cached_property
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
            bases = (b for b in bases if hasattr(b, '_meta') and
                     not b._meta.abstract)
            items = (r for r in (getattr(b, 'Reference', None) for b in bases)
                     if issubclass(r, Reference))
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
        new_class = super(ObjectBase, cls).__new__(cls, name, bases, attrs,
                                                   **kwargs)
        if new_class._meta.abstract:
            return new_class

        if reference_class is None:
            meta_class = Reference.__class__
            reference_class = meta_class.__new__(
                meta_class,
                name + 'Reference', (Reference,),
                {
                    'target': models.ForeignKey(
                        new_class, models.CASCADE, db_index=True,
                        related_name='reference_set',
                        verbose_name=_('Target'),
                    ),
                    '__module__': new_class.__module__,
                }
            )
            setattr(new_class, 'Reference', reference_class)
        return new_class


class ObjectQuerySet(models.QuerySet):
    """ QuerySet for Objects. """

    def ref(self, receiver: Agent, ref: UUID):
        """ Return reference for provided receiver and ref. """
        refs = self.model.Reference.objects.refs(receiver, [ref])
        fk_field = self.model.Reference._meta.get_field('target')
        lookup = fk_field.remote_field.get_accessor_name()
        prefetch = Prefetch(lookup, refs, '_agent_reference_set')

        refs = refs.filter(target=OuterRef('pk'))
        return self.annotate(reference_id=Subquery(refs.values('id')[:1])) \
                   .exclude(reference_id__isnull=True) \
                   .prefetch_related(prefetch) \
                   .get()

    def refs(self, receiver: Agent, refs: Iterable[UUID]):
        """ Return references for provided receiver and refs. """
        refs = self.model.Reference.objects.refs(receiver, refs)
        fk_field = self.model.Reference._meta.get_field('target')
        lookup = fk_field.remote_field.get_accessor_name()
        prefetch = Prefetch(lookup, refs, '_agent_reference_set')

        refs = refs.filter(target=OuterRef('pk'))
        return self.annotate(reference_id=Subquery(refs.values('id')[:1])) \
                   .exclude(reference_id__isnull=True) \
                   .prefetch_related(prefetch)


class Object(models.Model, metaclass=ObjectBase):
    """
    An object accessible through References.

    It can have a member `Reference` (subclass of `fox.caps.models.Reference`)
    that is used as object's specific reference. If none is provided, a
    it will be generated automatically for concrete classes.
    """
    objects = ObjectQuerySet.as_manager()

    agent_reference_set = None
    """
    QuerySet of references matching current object for an agent. Provided
    by ObjectQuerySet's `ref()`, `refs()`, otherwise None.
    """

    class Meta:
        abstract = True

    @cached_property
    def reference(self):
        """
        Return Reference to this object for receiver provided to
        ObjectQuerySet's `ref()` or `refs()`.
        """
        return self._agent_reference_set and self._agent_reference_set[0] \
            or None
