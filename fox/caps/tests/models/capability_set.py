from django.core.exceptions import PermissionDenied
from django.test import TransactionTestCase


__all__ = ('CapabilitySetTestCase',)


from fox.caps.models import Capability, CapabilitySet


class CapabilitySetTestCase(TransactionTestCase):
    # TODO: REDO
    def setUp(self):
        names = ['action_1', 'action_2', 'action_3']
        self.names = names
        self.caps_1 = [Capability(name=name, max_derive=2)
                       for i, name in enumerate(names)]
        self.caps_2 = [c.derive(names) for c in self.caps_1]
        Capability.objects.bulk_create(self.caps_1 + self.caps_2)

        self.set_1 = CapabilitySet(self.caps_1)
        self.set_1.save()
        self.set_2 = CapabilitySet(self.caps_2)
        self.set_2.save()

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
