"""API Django serializers."""
import re

import netaddr
from rest_framework import serializers
import validators

from api.models import Target
from plugins.interfaces import TargetInterface

REGEX_IPV4 = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)'
    r'{3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)
REGEX_IPV4_CIDR = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)'
    r'{3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    r'/(?:(?:3[0-2])|(?:[1-2]\d)|[1-9])$'
)
REGEX_IPV4_RANGE = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)'
    r'{3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    r'-'
    r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.)'
    r'{3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)
REGEX_DOMAIN = re.compile(
    r'^([a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.)+'
    r'[a-zA-Z]{2,}$'
)
REGEX_URL = re.compile(
    r'^(\*\.)?([a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.)+'
    r'[a-zA-Z]{2,}'
    r"/[-a-zA-Z0-9._~!$&'()*+,;=:@%#/?&]*$"
)
REGEX_MD5 = re.compile(r'^[0-9a-fA-F]{32}$')
REGEX_SHA1 = re.compile(r'^[0-9a-fA-F]{40}$')
REGEX_SHA256 = re.compile(r'^[0-9a-fA-F]{64}$')


def is_ipaddr_public(ipaddr):
    """Returns true if IP address is public."""
    return bool(ipaddr.is_unicast() and not ipaddr.is_private() and not
                ipaddr.is_loopback())


def verify_ip(target):
    """Verifies IP target."""
    if REGEX_IPV4.match(target):
        verify_ip_addr(target)
    elif REGEX_IPV4_CIDR.match(target):
        verify_ip_cidr(target)
    elif REGEX_IPV4_RANGE.match(target):
        verify_ip_range(target)
    else:
        raise serializers.ValidationError({'target': ['Invalid IP format.']})


def verify_ip_addr(ipaddr):
    """Verifies IP address."""
    try:
        ipaddr = netaddr.IPAddress(ipaddr)
    except netaddr.core.AddrFormatError:
        raise serializers.ValidationError(
            {'target': ['Invalid IP address.']})
    if not is_ipaddr_public(ipaddr):
        raise serializers.ValidationError(
            {'target': ['Only public IP addresses can be added.']})


def verify_ip_cidr(ipnet):
    """Verifies IP CIDR."""
    try:
        ipnet = netaddr.IPNetwork(ipnet)
    except netaddr.core.AddrFormatError:
        raise serializers.ValidationError(
            {'target': ['Invalid CIDR notation.']})
    if len(ipnet) > 65536:
        raise serializers.ValidationError(
            {'target': ['IP ranges are limited to a /16.']})
    if not is_ipaddr_public(ipnet):
        raise serializers.ValidationError(
            {'target': ['Only public IP addresses can be added.']})


def verify_ip_range(iprange):
    """Verifies IP address range."""
    iprange = iprange.split('-')
    try:
        iplist = list(netaddr.iter_iprange(iprange[0], iprange[1]))
    except netaddr.core.AddrFormatError:
        raise serializers.ValidationError(
            {'target': ['Invalid IP range notation.']})
    # iter_iprange may return an empty list instead of erroring
    if not iplist:
        raise serializers.ValidationError(
            {'target': ['Invalid IP range notation.']})
    if len(iplist) > 65536:
        raise serializers.ValidationError(
            {'target': ['IP ranges are limited to a /16.']})
    for ipaddr in iplist:
        if not is_ipaddr_public(ipaddr):
            raise serializers.ValidationError(
                {'target': ['Only public IP addresses can be added.']})


def verify_domain(domain):
    """Verifies if valid domain."""
    if REGEX_DOMAIN.match(domain):
        try:
            validators.domain(domain)
        except validators.ValidationFailure:
            raise serializers.ValidationError(
                {'target': ['Domain is not valid.']})
    else:
        raise serializers.ValidationError(
            {'target': ['Invalid domain format.']})


def verify_url(url):
    """Verifies if valid URL."""
    if REGEX_URL.match(url):
        try:
            validators.url('http://' + url.lstrip('*.'))
        except validators.ValidationFailure:
            raise serializers.ValidationError(
                {'target': ['URL is not valid.']})
    else:
        raise serializers.ValidationError(
            {'target': ['Invalid URL format.']})


def verify_hash(target):
    """Verifies if valid hash."""
    if not (REGEX_MD5.match(target) or REGEX_SHA1.match(target) or
            REGEX_SHA256.match(target)):
        raise serializers.ValidationError(
            {'target': ['Invalid hash format.']})


def verify_username(username):
    """Verifies if valid username."""
    try:
        # Windows Active Directory Logon Name rules
        # https://technet.microsoft.com/en-us/library/bb726984.aspx
        validators.length(username, min=1, max=104)
        invalid_chars = list('/\\[]":;|<>+=,?*@')
        if any(c in invalid_chars for c in username):
            raise serializers.ValidationError(
                {'target': [
                    'Username cannot contain the following characters: %s' % (
                        ''.join(invalid_chars))
                ]}
            )
    except validators.ValidationFailure:
        raise serializers.ValidationError(
            {'target': ['Username is not valid.']})


def verify_plugin_method(target, target_type, requested_method):
    """Verifies that the plugin method is valid."""
    target = TargetInterface(target, target_type)
    if requested_method.lower() == 'none':
        return
    elif requested_method in target.methods:
        return
    raise serializers.ValidationError(
        {'method': ['Invalid plugin method.']})


def whitelisted(target, target_type):
    """Checks if the target has already been added as an Allow."""
    try:
        Target.objects.get(
            target=target, target_type=target_type, target_action=Target.ALLOW)
    except Target.DoesNotExist:
        return False
    return True


class TargetSerializer(serializers.ModelSerializer):
    """Definition of a Target Serializer."""
    user = serializers.CharField(
        read_only=True,
        max_length=255,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Target
        fields = (
            'id',
            'target',
            'target_action',
            'target_type',
            'method',
            'reason',
            'user',
            'date_created',
            'last_modified',
        )
        read_only_fields = (
            'user',
            'date_created',
            'last_modified',
        )

    def validate(self, data):
        target = data['target']
        target_type = data['target_type']
        method = data['method']

        if target_type == Target.IPADDR:
            verify_ip(target)
            verify_plugin_method(target, target_type, method)
        elif target_type == Target.DOMAIN:
            verify_domain(target)
            verify_plugin_method(target, target_type, method)
        elif target_type == Target.URL:
            verify_url(target)
            verify_plugin_method(target, target_type, method)
        elif target_type == Target.HASH:
            verify_hash(target)
            verify_plugin_method(target, target_type, method)
        elif target_type == Target.USER:
            verify_username(target)
            verify_plugin_method(target, target_type, method)

        if whitelisted(target, target_type):
            raise serializers.ValidationError(
                {'target': ['Target is whitelisted and cannot be banned.']})

        return data
