from django.core.exceptions import PermissionDenied
from django.test import TestCase


__all__ = ('ReferenceTestCase',)


from fox.caps.models import Agent, Capability, Reference


class ReferenceTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        agents = Agent(), Agent(), Agent()
        Agent.objects.bulk_create(agents)

        cls.emitter, cls.receiver, cls.agent = agents
        cls.actions = ['action_1', 'action_2', 'action_3', 'action_4']

