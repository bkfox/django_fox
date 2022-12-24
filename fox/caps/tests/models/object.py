from django.test import TestCase
from .reference import BaseReferenceTestCase


__all__ = ('ObjectManagerTestCase', 'ObjectQuerySetTestCase',)


class ObjectManagerTestCase(TestCase):
    def test_get_reference_class_from_attrs(self):
        pass

    def test_get_reference_class_from_bases(self):
        pass

    def test_new_with_reference(self):
        pass

    def test_new_fail_not_reference_subclass(self):
        pass

    def test_new_generate_reference(self):
        pass


class ObjectQuerySetTestCase(BaseReferenceTestCase):
    pass
