from django.core.exceptions import PermissionDenied
from django.test import TransactionTestCase


__all__ = ('CapabilitySetTestCase',)


from fox.caps.models import Capability, CapabilitySet


# Test both CapabilitySet and BaseCapabilitySet
class CapabilitySetTestCase(TransactionTestCase):
    # TODO: derive_caps, aderive_caps, aderive
    @classmethod
    def setUpClass(cls):
        names = ['action_1', 'action_2', 'action_3']
        cls.names = names
        cls.caps_1 = [Capability(name=name, max_derive=2)
                      for i, name in enumerate(names)]
        cls.caps_2 = [c.derive() for c in cls.caps_1]

        cls.set_1 = CapabilitySet(cls.caps_1)
        cls.set_2 = CapabilitySet(cls.caps_2)

    def test_is_derived(self):
        self.assertTrue(self.set_1.is_derived(self.set_2))
        self.assertFalse(self.set_2.is_derived(self.set_1))

    def test_is_derived_with_missing_in_parent(self):
        subset = CapabilitySet(self.caps_2)
        cap = Capability(name='missing_one', max_derive=10)
        subset.capabilities.append(cap)
        self.assertFalse(self.set_1.is_derived(subset))

    def test_derive_caps_without_arg(self):
        expected = [Capability(name=name, max_derive=0)
                    for name in self.names]
        capabilities = self.set_1.derive_caps()
        self.assertCountEqual(expected, capabilities)

    def test_derive_caps_with_string_list_arg(self):
        expected = [Capability(name=name, max_derive=0) for name in self.names]
        capabilities = self.set_1.derive_caps(self.names)
        self.assertCountEqual(expected, capabilities)

    def test_derive_caps_with_tuple_list_arg(self):
        args = [(name, i % 2) for i, name in enumerate(self.names)]
        expected = [Capability(name=name, max_derive=i) for name, i in args]
        capabilities = self.set_1.derive_caps(args)
        self.assertCountEqual(expected, capabilities)

    def test_derive_caps_fail_missing_cap(self):
        with self.assertRaises(PermissionDenied):
            self.set_1.derive_caps(self.names + ['missing_one'])

    def test_derive_caps_fail_cap_not_derived(self):
        with self.assertRaises(PermissionDenied):
            caps = self.names[:-1] + [(self.names[-1], 10)]
            self.set_2.derive_caps(caps)

    def test_derive_caps_fail_cant_derive(self):
        caps = self.set_2.derive_caps(self.names)
        set = CapabilitySet(caps)
        with self.assertRaises(PermissionDenied):
            set.derive_caps(self.names)
