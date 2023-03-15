import pytest
from django.test import RequestFactory

import fox.caps.views.mixins as mixins
from fox.caps.models import Agent

factory = RequestFactory()


@pytest.fixture
def agent(db):
    agent = Agent()
    agent.save()
    return agent


@pytest.fixture
def objects(db):
    pass


@pytest.fixture
def base_object_mixin(rf, agent):
    request = rf.get("/test")
    setattr(request, "agent", agent)
    mixin = mixins.BaseObjectMixin()
    mixin.request = request


class TestBaseObjectMixin:
    def test_get_agent(self, base_object_mixin, agent):
        assert base_object_mixin.get_agent() is agent


class TestObjectListMixin:
    def test_get_queryset(self):
        pass


class TestObjectDetailMixin:
    def test_get_object(self):
        pass
