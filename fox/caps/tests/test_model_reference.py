import copy

import pytest

from fox.utils.test import assertCountEqual
from .app.models import ConcreteReference

__all__ = ("TestReference", "TestReferenceQuerySet")


class TestReference:
    def test_is_valid(self, refs):
        assert refs[2].is_valid()
        assert refs[1].is_valid()
        assert refs[0].is_valid()

    def test_is_valid_invalid_depth(self, refs_3, refs_1):
        ref = copy.copy(refs_1[0])
        ref.depth = refs_3[0].depth
        with pytest.raises(ValueError):
            ref.is_valid()
        ref.depth = 0
        with pytest.raises(ValueError):
            ref.is_valid()

    def test_is_derived(self, refs_3, refs_2):
        for ref in refs_3:
            derives = {r for r in refs_2 if r.target == ref.target}
            for derived in derives:
                assert ref.is_derived(derived)
                assert not derived.is_derived(ref)

    def test_is_derived_wrong_depth(self, refs):
        ref = refs[2].derive(refs[1].receiver)
        ref.depth = refs[2].depth
        assert not refs[2].is_derived(ref)

    def test_is_derived_wrong_target(self, refs, objects):
        ref = refs[2].derive(refs[1].receiver)
        ref.target = objects[1]
        assert not refs[2].is_derived(ref)

    # caps: caps_3 (used by refs_3
    def test_create(self, refs, agents, caps):
        capabilities = list(refs[0].get_capabilities())
        assert agents[0] == refs[0].emitter
        assert agents[0] == refs[0].receiver
        assert 0 == refs[0].depth
        assertCountEqual(caps, capabilities)

    def test_create_fail_origin(self, agents, objects, caps, refs):
        with pytest.raises(ValueError):
            ConcreteReference.create(
                agents[0], objects[1], caps, origin=refs[0]
            )

    def test_derive(self):
        # tested through setUpClass and is_derived/valid
        pass


class TestReferenceQuerySet:
    def test_emitter(self, agents):
        for agent in agents:
            for ref in ConcreteReference.objects.emitter(agent):
                assert (
                    agent == ref.emitter
                ), "for agent {}, ref: {}, ref.emitter: {}".format(
                    agent.ref, ref, ref.emitter.ref
                )

    def test_receiver(self, agents):
        for agent in agents:
            for ref in ConcreteReference.objects.receiver(agent):
                assert (
                    agent == ref.receiver
                ), "for agent {}, ref: {}, ref.receiver: {}".format(
                    agent.ref, ref, ref.receiver.ref
                )

    def test_ref(self, refs):
        for ref in refs:
            item = ConcreteReference.objects.ref(ref.receiver, ref.ref)
            assert ref == item

    def test_ref_wrong_agent(self, refs, agents):
        for ref in refs:
            for agent in agents:
                if ref.receiver == agent:
                    continue
                with pytest.raises(
                    ConcreteReference.DoesNotExist,
                    msg="ref: {}, agent: {}".format(ref, agent.ref),
                ):
                    ConcreteReference.objects.ref(agent, ref.ref)

    def test_refs(self, agents, refs):
        for agent in agents:
            refs = [ref for ref in refs if ref.receiver == agent]
            queryset = ConcreteReference.objects.refs(
                agent, set(r.ref for r in refs)
            )
            items = list(queryset)
            assertCountEqual(refs, items, "agent: " + str(agent.ref))

    def test_refs_wrong_agent(self, agents, refs):
        for agent in agents:
            refs = [ref for ref in refs if ref.receiver != agent]
            queryset = ConcreteReference.objects.refs(
                agent, set(r.ref for r in refs)
            )
            assert not queryset.exists(), "agent: " + str(agent.ref)

    # TODO: bulk_create, bulk_update
