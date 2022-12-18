from django.middleware import

from .models import Context, SiteContext


__all__ = ('AgentMiddleware',)


class AgentMiddleware:
    """
    Provides identities for request's user.

    Current identity id can be specified with ``pepr.core.identity``
    cookie.

    Request will have two extra attributes:
    - ``identity``: current identity;
    - ``identities``: queryset of all available identities for user;
    - ``role``: current site role;
    """
    context_class = Context

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.get_identity(request)
        self.get_role(request)
        return self.get_response(request)

    def get_identity(self, request):
        if not hasattr(request, 'user'):
            raise RuntimeError(
                "AgentMiddleware requires Django's AuthenticationMiddleware.")
        identity, identities = self.context_class.objects.get_identities(
            request.user, request.COOKIES.get('pepr.core.identity')
        )
        if identity:
            identity.identity_user = request.user

        request.identity, request.identities = identity, identities

    def get_role(self, request):
        """ Get user's role for current site. """
        if not hasattr(request, 'site'):
            raise RuntimeError(
                "AgentMiddleware requires Django's CurrentSiteMiddleware")

        context = getattr(request.site, 'site_context', None)
        if context is None:
            context = self.create_site_context(request.site)
        request.role = context and context.get_role(request.identity)

    def create_site_context(self, site, save=True, **kwargs):
        """ Create context for request's site. """
        context = SiteContext(site=site, **kwargs)
        if save:
            context.save()
        return context


