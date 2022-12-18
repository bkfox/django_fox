from asgiref.sync import sync_to_async

from django.core.exceptions import PermissionDenied
from django.test import TestCase


__all__ = ('CapabilityQuerySetTestCase', 'CapabilityTestCase',)


from fox.caps.models import Capability, CapabilitySet


class CapabilityQuerySetTestCase(TestCase):
    def test_get_or_create_many(self):
        subset = [Capability(name='action_1', max_derive=1),
                  Capability(name='action_2', max_derive=1)]
        subset[0].save()
        result = Capability.objects.get_or_create_many(subset)

        self.assertEqual(len(subset), result.count())
        for item in subset:
            self.assertIsNotNone(item.pk)

    async def test_aget_or_create_many(self):
        subset = [Capability(name='action_1', max_derive=1),
                  Capability(name='action_2', max_derive=1)]
        sync_to_async(subset[0].save)
        result = await Capability.objects.aget_or_create_many(subset)

        self.assertEqual(len(subset), await result.acount())
        for item in subset:
            self.assertIsNotNone(item.pk)

    # TODO: test__get_items_queryset


class CapabilityTestCase(TestCase):
    def test_into_tuple(self):
        expected = Capability(name='action', max_derive=12)
        values = (
            (expected.name, expected.max_derive),
            [expected.name, expected.max_derive],
            {'name': expected.name, 'max_derive': expected.max_derive},
            Capability(name=expected.name, max_derive=expected.max_derive))
        for value in values:
            capability = Capability.into(value)
            self.assertEqual(expected, capability)

    def test_into_raises(self):
        with self.assertRaises(NotImplementedError):
            Capability.into(12.1)

    def test_can_derive(self):
        self.assertFalse(Capability(max_derive=0).can_derive())
        self.assertTrue(Capability(max_derive=1).can_derive())
        self.assertTrue(Capability(max_derive=2).can_derive())

    def test_derive(self):
        parent = Capability(name='test', max_derive=1)
        child = parent.derive()
        self.assertEqual(parent.name, child.name)
        self.assertEqual(parent.max_derive-1, child.max_derive)

    def test_derive_fail(self):
        parent = Capability(name='test', max_derive=0)
        with self.assertRaises(PermissionDenied):
            parent.derive()

    def test_is_derived(self):
        parent = Capability(name='test', max_derive=3)
        child = parent.derive()
        self.assertTrue(parent.is_derived(child))
        # test reverse relation direction
        self.assertFalse(child.is_derived(parent))

    def test_is_derived_false_max_derive(self):
        parent = Capability(name='test', max_derive=1)
        child = Capability(name='test', max_derive=2)
        self.assertFalse(parent.is_derived(child))

    def test_is_derived_leaf_false(self):
        parent = Capability(name='test', max_derive=0)
        child = Capability(name='test', max_derive=-1)
        self.assertFalse(parent.is_derived(child))

    def test_is_derived_nested(self):
        parent = Capability(name='test', max_derive=4)
        child = parent.derive().derive().derive()
        self.assertTrue(parent.is_derived(child))


class CapabilitySetTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        names = ['action_1', 'action_2', 'action_3']
        cls.names = names
        cls.caps_1 = [Capability(name=name, max_derive=2)
                      for i, name in enumerate(names)]
        cls.caps_2 = [c.derive(names) for c in cls.caps_1]
        Capability.objects.bulk_create(cls.caps_1 + cls.caps_2)

        cls.set_1 = CapabilitySet(cls.caps_1)
        cls.set_2 = CapabilitySet(cls.caps_2)

    def test_is_derived(self):
        self.assertTrue(self.set_1.is_derived(self.set_2))
        self.assertFalse(self.set_2.is_derived(self.set_1))

    def test_is_derived_with_missing_in_parent(self):
        subset = CapabilitySet(self.caps_2)
        cap = Capability(name='missing_one', max_derive=10)
        subset.add(cap)
        self.assertFalse(self.set_1.is_derived(subset))

    def test_derive(self):
        capabilities = self.set_1.derive(self.names)
        self.assertEqual(self.set_2, capabilities)

    def test_derive_fail_missing_cap(self):
        with self.assertRaises(PermissionDenied):
            self.set_1.derive(self.names + ['missing_one'])

    def test_derive_fail_cap_not_derived(self):
        with self.assertRaises(PermissionDenied):
            caps = self.name[:-1] + [(self.names[-1], 10)]
            self.set_2.derive(caps)

    def test_derive_fail_cant_derive(self):
        set = self.set_2.derive(self.names)
        with self.assertRaises(PermissionDenied):
            set.derive(self.names)

    def test_add(self):
        set = CapabilitySet()
        capability = Capability(name='action', max_derive=1)
        set.add(capability)
        self.assertEqual('action', set['action'].name)
        with self.assertRaises(KeyError):
            set.add(capability)

    def test_extend(self):
        set = CapabilitySet()
        set.extend([Capability(name='action', max_derive=1)])
        self.assertEqual('action', set['action'].name)

    # TODO: test getters and setters, add, extend 
