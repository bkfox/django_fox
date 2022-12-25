from django.db import models
from django.test import TestCase

from .reference import BaseReferenceTestCase
from fox.caps.models import Reference
from fox.caps.models.object import Object, ObjectBase, ObjectQuerySet


__all__ = ('ObjectManagerTestCase', 'ObjectQuerySetTestCase',)


class ParentConcrete(Object):
    name = models.CharField(max_length=16)


class ParentAbstract(Object):
    name = models.CharField(max_length=16)

    # Force reference sub-class to cover more fields
    class Reference(Reference):
        # need a concrete type here.
        target = models.ForeignKey(ParentConcrete, models.CASCADE,
                                   related_name='_llk')

    class Meta:
        abstract = True


class ObjectManagerTestCase(TestCase):
    def test_get_reference_class_from_attrs(self):
        result = ObjectBase.get_reference_class('test', (Object,), attrs={
            'Reference': Reference})
        self.assertIs(Reference, result)

    def test_get_reference_class_from_attrs_fail_reference_not_subclass(self):
        with self.assertRaises(ValueError):
            ObjectBase.get_reference_class(
                'test', (Object,),
                attrs={'Reference': object, '__module__': self.__module__})

    def test_get_reference_class_from_bases(self):
        result = ObjectBase.get_reference_class(
            'test', (ParentAbstract, ParentConcrete,),
            attrs={'__module__': self.__module__})
        self.assertIsNot(ParentAbstract.Reference, result,
                         "result should not return an abstract class")
        self.assertIs(ParentConcrete.Reference, result)

    def test_new_with_reference(self):
        result = ObjectBase.__new__(ObjectBase, 'test', (ParentConcrete,),
                                    {'__module__': self.__module__})
        self.assertTrue(issubclass(result, ParentConcrete))
        self.assertTrue(issubclass(result.Reference, Reference))

    def test_new_generate_reference(self):
        result = ObjectBase.__new__(ObjectBase, 'test', (Object,),
                                    {'__module__': self.__module__})
        self.assertTrue(issubclass(result, Object))
        self.assertTrue(issubclass(result.Reference, Reference))


class ObjectQuerySetTestCase(BaseReferenceTestCase):
    def test_ref(self):
        for ref in self.refs:
            result = self.TestObject.objects.ref(ref.receiver, ref.ref)
            self.assertIsNotNone(result)
            self.assertEqual(ref, result.reference)

    def test_ref_wrong_agent(self):
        for ref in self.refs:
            agents = (r for r in self.agents if r != ref.receiver)
            for agent in agents:
                with self.assertRaises(self.TestObject.DoesNotExist):
                    self.TestObject.objects.ref(agent, ref.ref)

    def test_refs(self):
        for agent in self.agents:
            refs = [r for r in self.refs if r.receiver == agent]
            result = self.TestObject.objects.refs(agent, [r.ref for r in refs])
            self.assertCountEqual(refs, (r.reference for r in result))

    def test_refs_wrong_refs(self):
        for agent in self.agents:
            refs = [r for r in self.refs if r.receiver != agent]
            result = self.TestObject.objects.refs(agent, [r.ref for r in refs])
            self.assertFalse(result.exists())

