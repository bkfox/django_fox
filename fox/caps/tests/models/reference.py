import copy

from django.db import models
from fox.utils.tests import ModelMixinTestCase
from fox.caps.models import Agent, Capability, Object


__all__ = ('ReferenceTestCase', 'ReferenceQuerySetTestCase')


class BaseReferenceTestCase(ModelMixinTestCase):
    class TestObject(Object):
        name = models.CharField(max_length=16)

    TestReference = TestObject.Reference

    _set_up_done = False

    @classmethod
    def setUpClass(cls):
        super(BaseReferenceTestCase, cls).setUpClass()
        if cls._set_up_done:
            return

        cls.agents = Agent(), Agent(), Agent()
        Agent.objects.bulk_create(cls.agents)

        cls.actions = ['action_1', 'action_2']
        caps = [Capability(name=r, max_derive=3) for r in cls.actions]
        cls.caps = list(Capability.objects.get_or_create_many(caps))

        cls.objects = [cls.TestObject(name='object_0'),
                       cls.TestObject(name='object_1'),
                       cls.TestObject(name='object_2')]
        cls.TestObject.objects.bulk_create(cls.objects)

        cls.refs_3 = [
            cls.TestReference.create(cls.agents[0], cls.objects[0], cls.caps),
            cls.TestReference.create(cls.agents[1], cls.objects[1], cls.caps),
            cls.TestReference.create(cls.agents[2], cls.objects[2], cls.caps),
        ]
        caps = [(n, 2) for n in cls.actions]
        cls.refs_2 = [cls.refs_3[0].derive(cls.agents[1], caps),
                      cls.refs_3[1].derive(cls.agents[2], caps),
                      cls.refs_3[2].derive(cls.agents[0], caps)]
        cls.refs_1 = [cls.refs_2[0].derive(cls.agents[2]),
                      cls.refs_2[1].derive(cls.agents[0]),
                      cls.refs_2[2].derive(cls.agents[1])]
        cls.refs = cls.refs_3 + cls.refs_2 + cls.refs_1


class ReferenceTestCase(BaseReferenceTestCase):
    def test_is_valid(self):
        self.assertTrue(self.refs[2].is_valid())
        self.assertTrue(self.refs[1].is_valid())
        self.assertTrue(self.refs[0].is_valid())

    def test_is_valid_invalid_depth(self):
        ref = copy.copy(self.refs_1[0])
        ref.depth = self.refs_3[0].depth
        with self.assertRaises(ValueError):
            ref.is_valid()
        ref.depth = 0
        with self.assertRaises(ValueError):
            ref.is_valid()

    def test_is_derived(self):
        for ref in self.refs_3:
            derives = {r for r in self.refs_2 if r.target == ref.target}
            for derived in derives:
                self.assertTrue(ref.is_derived(derived))
                self.assertFalse(derived.is_derived(ref))

    def test_is_derived_wrong_depth(self):
        ref = self.refs[2].derive(self.refs[1].receiver)
        ref.depth = self.refs[2].depth
        self.assertFalse(self.refs[2].is_derived(ref))

    def test_is_derived_wrong_target(self):
        ref = self.refs[2].derive(self.refs[1].receiver)
        ref.target = self.objects[1]
        self.assertFalse(self.refs[2].is_derived(ref))

    def test_create(self):
        capabilities = list(self.refs[0].get_capabilities())
        self.assertEqual(self.agents[0], self.refs[0].emitter)
        self.assertEqual(self.agents[0], self.refs[0].receiver)
        self.assertEqual(0, self.refs[0].depth)
        self.assertCountEqual(self.caps, capabilities)

    def test_create_fail_origin(self):
        with self.assertRaises(ValueError):
            self.TestReference.create(self.agents[0], self.objects[1],
                                      self.caps, origin=self.refs[0])

    def test_derive(self):
        # tested through setUpClass and is_derived/valid
        pass


class ReferenceQuerySetTestCase(BaseReferenceTestCase):
    def test_emitter(self):
        for agent in self.agents:
            for ref in self.TestReference.objects.emitter(agent):
                self.assertEqual(agent, ref.emitter,
                                 'for agent {}, ref: {}, ref.emitter: {}'
                                 .format(agent.ref, ref, ref.emitter.ref))

    def test_receiver(self):
        for agent in self.agents:
            for ref in self.TestReference.objects.receiver(agent):
                self.assertEqual(agent, ref.receiver,
                                 'for agent {}, ref: {}, ref.receiver: {}'
                                 .format(agent.ref, ref, ref.receiver.ref))

    test_ref_queryset = BaseReferenceTestCase.TestReference

    def test_ref(self):
        for ref in self.refs:
            item = self.test_ref_queryset.objects.ref(ref.receiver, ref.ref)
            self.assertEqual(ref, item)

    def test_ref_wrong_agent(self):
        for ref in self.refs:
            for agent in self.agents:
                if ref.receiver == agent:
                    continue
                with self.assertRaises(self.TestReference.DoesNotExist,
                                       msg='ref: {}, agent: {}'.format(
                                           ref, agent.ref)):
                    self.test_ref_queryset.objects.ref(agent, ref.ref)

    def test_refs(self):
        for agent in self.agents:
            refs = [ref for ref in self.refs if ref.receiver == agent]
            queryset = self.test_ref_queryset.objects \
                           .refs(agent, set(r.ref for r in refs))
            items = list(queryset)
            self.assertCountEqual(refs, items, 'agent: ' + str(agent.ref))

    def test_refs_wrong_agent(self):
        for agent in self.agents:
            refs = [ref for ref in self.refs if ref.receiver != agent]
            queryset = self.test_ref_queryset.objects \
                           .refs(agent, set(r.ref for r in refs))
            self.assertFalse(queryset.exists(), 'agent: ' + str(agent.ref))

    # TODO: bulk_create, bulk_update
