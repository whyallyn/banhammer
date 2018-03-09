"""Djangosaml2 Django views."""
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT, entity
from saml2.client import Saml2Client
from saml2.config import Config

from django.conf import settings
from django.contrib.auth.models import (User, Group)
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.module_loading import import_string
from django.views.decorators.csrf import csrf_exempt


def get_current_domain(request):
    """Get domain with scheme."""
    return '{scheme}://{host}'.format(
        scheme='https' if request.is_secure() else 'http',
        host=request.get_host(),
    )


def get_saml_client(domain):
    """Get SAML2 client."""
    acs_url = domain + reverse('djangosaml2:acs')
    saml_settings = {
        'metadata': {
            'remote': [{
                'url': settings.SAML2_AUTH['METADATA_AUTO_CONF_URL']
            }]
        },
        'service': {
            'sp': {
                'endpoints': {
                    'assertion_consumer_service': [
                        (acs_url, BINDING_HTTP_REDIRECT),
                        (acs_url, BINDING_HTTP_POST)
                    ],
                },
                'allow_unsolicited': True,
                'authn_requests_signed': True,
                'logout_requests_signed': True,
                'want_assertions_signed': True,
                'want_response_signed': True,
            },
        },
    }

    sp_config = Config()
    sp_config.load(saml_settings)
    sp_config.allow_unknown_attributes = True
    saml_client = Saml2Client(config=sp_config)
    return saml_client


def denied(request):
    """Authentication failed and user was denied."""
    return render(request, 'djangosaml2/denied.html')


def add_user_to_groups(user, list_of_groups):
    """Add user to groups that exist."""
    for grp in list_of_groups:
        if Group.objects.filter(name=grp).exists():
            group = Group.objects.get(name=grp)
            user.groups.add(group)


def create_new_user(username, email, firstname, lastname, groups):
    """Create a new user from SAML information."""
    user = User.objects.create_user(username, email)
    user.first_name = firstname
    user.last_name = lastname
    add_user_to_groups(user, groups)
    user.is_active = settings.SAML2_AUTH.get(
        'NEW_USER_PROFILE', {}).get('ACTIVE_STATUS', True)
    user.is_staff = settings.SAML2_AUTH.get(
        'NEW_USER_PROFILE', {}).get('STAFF_STATUS', True)
    user.is_superuser = settings.SAML2_AUTH.get(
        'NEW_USER_PROFILE', {}).get('SUPERUSER_STATUS', False)
    user.save()
    return user


@csrf_exempt
def acs(request):
    """SAML Assertion Consumer Service endpoint."""
    saml_client = get_saml_client(get_current_domain(request))
    resp = request.POST.get('SAMLResponse', None)
    next_url = request.session.get('login_next_url', reverse('web:index'))

    if not resp:
        return HttpResponseRedirect(reverse('djangosaml2:denied'))

    authn_response = saml_client.parse_authn_request_response(
        resp, entity.BINDING_HTTP_POST)
    if authn_response is None:
        return HttpResponseRedirect(reverse('djangosaml2:denied'))

    user_identity = authn_response.get_identity()
    if user_identity is None:
        return HttpResponseRedirect(reverse('djangosaml2:denied'))

    user_email = user_identity[settings.SAML2_AUTH.get(
        'ATTRIBUTES_MAP', {}).get('email', None)][0]
    user_name = user_identity[settings.SAML2_AUTH.get(
        'ATTRIBUTES_MAP', {}).get('username', None)][0]
    user_first_name = user_identity[settings.SAML2_AUTH.get(
        'ATTRIBUTES_MAP', {}).get('first_name', None)][0]
    user_last_name = user_identity[settings.SAML2_AUTH.get(
        'ATTRIBUTES_MAP', {}).get('last_name', None)][0]
    user_groups = user_identity[settings.SAML2_AUTH.get(
        'ATTRIBUTES_MAP', {}).get('groups', [])]

    target_user = None
    try:
        target_user = User.objects.get(username=user_name)
        # update user groups
        target_user.groups.clear()
        add_user_to_groups(target_user, user_groups)
        target_user.save()
        if settings.SAML2_AUTH.get('TRIGGER', {}).get('BEFORE_LOGIN', None):
            import_string(
                settings.SAML2_AUTH['TRIGGER']['BEFORE_LOGIN'])(user_identity)
    except User.DoesNotExist:
        target_user = create_new_user(
            user_name, user_email, user_first_name, user_last_name, user_groups)
        if settings.SAML2_AUTH.get('TRIGGER', {}).get('CREATE_USER', None):
            import_string(
                settings.SAML2_AUTH['TRIGGER']['CREATE_USER'])(user_identity)

    request.session.flush()

    if target_user.is_active:
        target_user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, target_user)
    else:
        return HttpResponseRedirect(reverse('djangosaml2:denied'))

    return HttpResponseRedirect(next_url)


def signin(request):
    """Signin redirect."""
    return HttpResponseRedirect(settings.SAML2_AUTH['SSP_LOGIN_URL'])
