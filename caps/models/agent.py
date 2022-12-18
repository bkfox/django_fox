from __future__ import annotations
import uuid

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.models import User, Group


__all__ = ('AgentQuerySet', 'Agent')


class AgentQuerySet(models.QuerySet):
    def user(self, user: User) -> AgentQuerySet:
        """ Filter by user or its groups. """
        return self.filter(Q(user=user) | Q(group__in=user.groups.all())) \
                   .distinct()

    def group(self, group: Group) -> AgentQuerySet:
        """ Filter by group. """
        return self.filter(group=group)


class Agent(models.Model):
    """
    An agent is the one that actually execute an action. It can either be
    a user or a group.
    """
    ref = models.UUIDField(_('Public Reference'), default=uuid.uuid4)
    user = models.ForeignKey(User, models.CASCADE, null=True, blank=True,
                             verbose_name=_('User'))
    group = models.ForeignKey(Group, models.CASCADE, null=True, blank=True,
                              verbose_name=_('Group'))

    objects = AgentQuerySet.as_manager()
