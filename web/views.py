"""Web Django views."""
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework.authtoken.models import Token

from banhammer.settings import WEB_AUTH_ENABLED


class conditional_decorator(object):
    """Conditional decorator."""
    def __init__(self, dec, condition):
        self.decorator = dec
        self.condition = condition

    def __call__(self, func):
        if not self.condition:
            # Return the function unchanged, not decorated.
            return func
        return self.decorator(func)


def web_render(request, template, status=200):
    """Render web page with all required fields."""
    if request.user.is_authenticated():
        return render(
            request,
            template,
            {
                'user': request.user.first_name,
                'schema': 'https' if request.is_secure() else 'http',
                'token': 'None',  # Token.objects.get(user=request.user),
            },
            status=status
        )
    else:
        return render(
            request,
            template,
            {
                'user': 'Anon',
                'schema': 'https' if request.is_secure() else 'http',
                'token': 'None',
            },
            status=status
        )


@conditional_decorator(login_required, WEB_AUTH_ENABLED)
def ban(request):
    """Add a new ban."""
    return web_render(request, 'web/ban.html')


@conditional_decorator(login_required, WEB_AUTH_ENABLED)
def allow(request):
    """Add to the whiteslist."""
    return web_render(request, 'web/allow.html')


@conditional_decorator(login_required, WEB_AUTH_ENABLED)
def blist(request):
    """List bans."""
    return web_render(request, 'web/list.html')


@conditional_decorator(login_required, WEB_AUTH_ENABLED)
def docs(request):
    """API docs."""
    return web_render(request, 'web/docs.html')


def signout(request):
    """Logout the user."""
    logout(request)
    return render(request, 'web/signout.html')
