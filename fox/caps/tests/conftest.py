import pytest
from django.contrib.auth.models import Group, User

from fox.caps.models import Agent, Capability, CapabilitySet
from .app.models import ConcreteObject, ConcreteReference


# -- Agent
@pytest.fixture
def groups(db):
    groups = [Group(name="group_1"), Group(name="group_2")]
    Group.objects.bulk_create(groups)
    return groups


@pytest.fixture
def user(db, groups):
    user = User.objects.create_user(username="test_1", password="none")
    user.groups.add(groups[0])
    return user


@pytest.fixture
def agents(db, groups, user):
    agents = [Agent(user=user)] + [Agent(group=group) for group in groups]
    Agent.objects.bulk_create(agents)
    return agents


# -- Capabilities
@pytest.fixture
def caps_names():
    return ["action_1", "action_2", "action_3"]


@pytest.fixture
def caps_3(caps_names):
    return [
        Capability(name=name, max_derive=2)
        for i, name in enumerate(caps_names)
    ]


@pytest.fixture
def caps_2(caps_3):
    return [c.derive() for c in caps_3]


@pytest.fixture
def caps_1(caps_2):
    return [c.derive() for c in caps_2]


@pytest.fixture
def caps_set_2(caps_2):
    return CapabilitySet(caps_2)


@pytest.fixture
def caps_set_1(caps_1):
    return CapabilitySet(caps_1)


# -- Objects
@pytest.fixture
def objects(db):
    objects = [
        ConcreteObject(name="object_0"),
        ConcreteObject(name="object_1"),
        ConcreteObject(name="object_2"),
    ]
    ConcreteObject.objects.bulk_create(objects)
    return objects


@pytest.fixture
def refs_3(agents, objects, caps_3):
    # caps_3: all action, derive 3
    return [
        ConcreteReference.create(agents[0], objects[0], caps_3),
        ConcreteReference.create(agents[1], objects[1], caps_3),
        ConcreteReference.create(agents[2], objects[2], caps_3),
    ]


@pytest.fixture
def refs_2(refs_3, agents, caps_2):
    # caps_2: all actions, derive 2
    # FIXME: TestReference.test_create
    return [
        refs_3[0].derive(agents[1], caps_2),
        refs_3[1].derive(agents[2], caps_2),
        refs_3[2].derive(agents[0], caps_2),
    ]


@pytest.fixture
def refs_1(refs_2, agents):
    return [
        refs_2[0].derive(agents[2]),
        refs_2[1].derive(agents[0]),
        refs_2[2].derive(agents[1]),
    ]


@pytest.fixture
def refs(refs_3, refs_2, refs_1):
    return refs_3 + refs_2 + refs_1
