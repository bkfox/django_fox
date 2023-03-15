from asgiref.sync import sync_to_async
from django.core.exceptions import PermissionDenied
from django.test import TestCase

__all__ = (
    "CapabilityQuerySetTestCase",
    "CapabilityTestCase",
)


from fox.caps.models import Capability


class CapabilityQuerySetTestCase(TestCase):
    def test_get_or_create_many(self):
        subset = [
            Capability(name="action_1", max_derive=1),
            Capability(name="action_2", max_derive=1),
        ]
        subset[0].save()
        result = Capability.objects.get_or_create_many(subset)

        self.assertEqual(len(subset), result.count())
        for item in subset:
            self.assertIsNotNone(item.pk)

    async def test_aget_or_create_many(self):
        subset = [
            Capability(name="action_1", max_derive=1),
            Capability(name="action_2", max_derive=1),
        ]
        sync_to_async(subset[0].save)
        result = await Capability.objects.aget_or_create_many(subset)

        self.assertEqual(len(subset), await result.acount())
        for item in subset:
            self.assertIsNotNone(item.pk)

    # TODO: test__get_items_queryset


class CapabilityTestCase(TestCase):
    def test_into_tuple(self):
        expected = Capability(name="action", max_derive=12)
        values = (
            (expected.name, expected.max_derive),
            [expected.name, expected.max_derive],
            Capability(name=expected.name, max_derive=expected.max_derive),
        )
        for value in values:
            capability = Capability.into(value)
            self.assertEqual(expected, capability)

        # TODO string -> max_derive=0

    def test_into_raises(self):
        with self.assertRaises(NotImplementedError):
            Capability.into(12.1)

    def test_can_derive(self):
        self.assertFalse(Capability(max_derive=0).can_derive())
        self.assertTrue(Capability(max_derive=1).can_derive())
        self.assertTrue(Capability(max_derive=2).can_derive())

    def test_derive(self):
        parent = Capability(name="test", max_derive=1)
        child = parent.derive()
        self.assertEqual(parent.name, child.name)
        self.assertEqual(parent.max_derive - 1, child.max_derive)

    def test_derive_fail(self):
        parent = Capability(name="test", max_derive=0)
        with self.assertRaises(PermissionDenied):
            parent.derive()

    def test_is_derived(self):
        parent = Capability(name="test", max_derive=3)
        child = parent.derive()
        self.assertTrue(parent.is_derived(child))
        # test reverse relation direction
        self.assertFalse(child.is_derived(parent))

    def test_is_derived_false_max_derive(self):
        parent = Capability(name="test", max_derive=1)
        child = Capability(name="test", max_derive=2)
        self.assertFalse(parent.is_derived(child))

    def test_is_derived_leaf_false(self):
        parent = Capability(name="test", max_derive=0)
        child = Capability(name="test", max_derive=-1)
        self.assertFalse(parent.is_derived(child))

    def test_is_derived_nested(self):
        parent = Capability(name="test", max_derive=4)
        child = parent.derive().derive().derive()
        self.assertTrue(parent.is_derived(child))
