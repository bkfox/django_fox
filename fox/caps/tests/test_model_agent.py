import pytest
from django.core.exceptions import ValidationError

from fox.caps.models import Agent

__all__ = ("TestAgentQuerySet", "TestAgent")


# TODO:
# - test anonymous users on QuerySet
class TestAgentQuerySet:
    def test_user(self, user):
        queryset = Agent.objects.user(user)
        user_agent = next((r for r in queryset if r.user), None)
        group_agents = [r for r in queryset if r.group]

        assert queryset.count() == 1 + len(group_agents)
        assert user_agent and user_agent.user
        assert user_agent.user.pk == user.pk
        assert user.groups.count() == len(group_agents)

        group_agent_ids = {r.group_id for r in group_agents}
        for group in user.groups.all():
            assert group.pk in group_agent_ids

    def test_group(self, groups):
        for group in groups:
            queryset = Agent.objects.group(group)
            assert queryset.count() == 1
            assert group == next(iter(queryset)).group


class TestAgent:
    def test_is_anonymous_return_true(self):
        agent = Agent()
        assert agent.is_anonymous

    def test_is_anonymous_return_false(self, agents):
        for agent in agents:
            assert agent.is_anonymous

    def test_clean_raises_on_user_and_group(self, user, groups):
        agent = Agent(user=user, group=groups[0])
        with pytest.raises(ValidationError):
            agent.clean()

    def test_clean_raises_on_is_default_not_allowed(self, groups):
        agent = Agent(group=groups[0], is_default=True)
        with pytest.raises(ValidationError):
            agent.clean()

    def test_clean_anonymous_is_default(self):
        agent = Agent()
        agent.clean()
