"""Provide Django testing utilities."""
import unittest

from django.db import connection, models
from django.test import TestCase

__all__ = ("ModelMixinTestCase",)


_test_case = unittest.TestCase()


def assertCountEqual(a, b):
    """Short-hand for unittest's assertCountEqual."""
    return _test_case.assertCountEqual(a, b)


class ModelMixinTestCase(TestCase):
    """Initialize tests models on setUpClass and cleanup on tearDownClass.
    Model classes can be provided two ways:

    - attribute `models`: list of models to create
    - if not provided: scan for concrete model in class members.
    """

    models = None

    @classmethod
    def setUpClass(cls):
        if cls.models is None:
            cls.models = tuple(
                member
                for member in (getattr(cls, attr) for attr in dir(cls))
                if isinstance(member, models.Model)
                and not member._meta.abstract
            )
        if cls.models:
            with connection.schema_editor() as schema_editor:
                for model in cls.models:
                    schema_editor.create_model(model)
        super(ModelMixinTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if cls.models:
            with connection.schema_editor() as schema_editor:
                for model in cls.models:
                    schema_editor.delete_model(model)
