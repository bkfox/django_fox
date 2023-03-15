__all__ = (
    "BaseObjectMixin",
    "ObjectListMixin",
    "ObjectDetailMixin",
)


class BaseObjectMixin:
    """Mixin providing functionalities to work with Object model."""

    def get_agent(self):
        return self.request.agent


class ObjectListMixin(BaseObjectMixin):
    """List mixin used to retrieve Object list."""

    def get_queryset(self):
        agent = self.get_agent()
        return super().get_queryset().receiver(agent)


class ObjectDetailMixin(BaseObjectMixin):
    """Detail mixin used to retrieve Object detail.

    Note: user's reference is fetched from `get_object`, not `get_queryset`.
    """

    lookup_field = "ref"

    def get_object(self):
        agent = self.get_agent()
        ref = self.kwargs[self.lookup_field]
        queryset = self.get_queryset()
        return queryset.ref(agent, ref)
