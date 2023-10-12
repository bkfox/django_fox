from django.db import models

from fox.caps.models import Object as Object
from fox.caps.models import Reference

__all__ = (
    "ConcreteObject",
    "ConcreteReference",
    "AbstractObject",
    "AbstractReference",
)


class ConcreteObject(Object):
    name = models.CharField(max_length=16)


ConcreteReference = ConcreteObject.Reference


class AbstractObject(Object):
    name = models.CharField(max_length=16)

    class Reference(Reference):
        target = models.ForeignKey(
            ConcreteObject, models.CASCADE, related_name="_abstract"
        )

    class Meta:
        abstract = True


AbstractReference = AbstractObject.Reference
