from django.http import HttpRequest

from .models import Agent, AgentQuerySet

__all__ = ("AgentMiddleware",)


class AgentMiddleware:
    """Fetch request user's active agent, and assign it to
    ``request.agent``."""

    agent_class = Agent
    """Agent model class to use."""
    agent_cookie_key = "fox.caps.agent"
    """Cookie used to get agent."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        agents = self.get_agents(request)
        request.agent = self.get_agent(request, agents)
        return self.get_response(request)

    def get_agents(self, request: HttpRequest) -> AgentQuerySet:
        """Return queryset for user's agents, ordered by ``-is_default``."""
        return Agent.objects.user(request.user, strict=False).order_by(
            "-is_default"
        )

    def get_agent(self, request: HttpRequest, agents: AgentQuerySet) -> Agent:
        """Return user's active agent."""
        cookie = request.COOKIES.get(self.agent_cookie_key)
        if cookie:
            # we iterate over agents instead of fetching extra queryset
            # this keeps cache for further operations.
            agent = next((r for r in agents if r.ref == cookie), None)
            if agent:
                return agent

        if request.user.is_anonymous:
            return next(agents, None)

        # agents are sorted such as default are first:
        # predicates order ensure that we return first on is_default
        # then only if is user
        return next(
            (
                r
                for r in agents
                if agent.is_default or agent.user_id == request.user.id
            ),
            None,
        )
