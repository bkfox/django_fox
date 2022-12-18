from django.test import TestCase

from django.contrib.auth.models import User, Group


__all__ = ('AgentQuerySetTestCase',)


from fox.caps.models import Agent


class AgentQuerySetTestCase(TestCase):
    def setUp(self):
        self.groups = [Group(name='group_1'),
                       Group(name='group_2')]
        Group.objects.bulk_create(self.groups)

        self.user = User.objects.create_user(username='test_1', password='none')
        self.user.groups.add(self.groups[0])

        self.agents = [Agent(user=self.user)] + \
                      [Agent(group=group) for group in self.groups]
        Agent.objects.bulk_create(self.agents)

    def test_user(self):
        queryset = Agent.objects.user(self.user)
        user_agent = next((r for r in queryset if r.user), None)
        group_agents = [r for r in queryset if r.group]

        self.assertEqual(queryset.count(), 1+len(group_agents))
        self.assertTrue(user_agent and user_agent.user)
        self.assertEqual(user_agent.user.pk, self.user.pk)
        self.assertEqual(self.user.groups.count(), len(group_agents))

        group_agent_ids = {r.group_id for r in group_agents}
        for group in self.user.groups.all():
            self.assertIn(group.pk, group_agent_ids)

    def test_group(self):
        for group in self.groups:
            queryset = Agent.objects.group(group)
            self.assertEqual(queryset.count(), 1)
            self.assertEqual(group, next(iter(queryset)).group)
