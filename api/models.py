"""API Django models."""
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Target(models.Model):
    """Definition of a Target."""
    BAN = 'ban'
    ALLOW = 'allow'
    TARGET_ACTION_CHOICES = (
        (BAN, "Ban"),
        (ALLOW, "Allow"),
    )
    target_action = models.CharField(
        max_length=5,
        choices=TARGET_ACTION_CHOICES,
    )

    IPADDR = 'ip'
    DOMAIN = 'domain'
    URL = 'url'
    HASH = 'hash'
    USER = 'user'
    TARGET_TYPE_CHOICES = (
        (IPADDR, 'IP Address'),
        (DOMAIN, 'Domain'),
        (URL, 'URL'),
        (HASH, 'Hash'),
        (USER, 'User'),
    )
    target_type = models.CharField(
        max_length=6,
        choices=TARGET_TYPE_CHOICES,
    )

    target = models.CharField(max_length=900)
    reason = models.CharField(max_length=50)
    method = models.CharField(max_length=50)
    user = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ('target_all_read', 'Read access for all Target types'),
            ('target_all_write', 'Write access for all Target types'),
            ('target_ipaddr_read', 'Read access for IP Target types'),
            ('target_ipaddr_write', 'Write access for IP Target types'),
            ('target_domain_read', 'Read access for Domain Target types'),
            ('target_domain_write', 'Write access for Domain Target types'),
            ('target_url_read', 'Read access for URL Target types'),
            ('target_url_write', 'Write access for URL Target types'),
            ('target_hash_read', 'Read access for Hash Target types'),
            ('target_hash_write', 'Write access for Hash Target types'),
            ('target_user_read', 'Read access for User Target types'),
            ('target_user_write', 'Write access for User Target types'),
        )

    def __str__(self):
        return self.target


@python_2_unicode_compatible
class TargetIpAddr(models.Model):
    """Definition of an IP Address Target."""
    ipaddr = models.CharField(max_length=45, unique=True)
    ipaddr_action = models.CharField(
        max_length=5,
        choices=Target.TARGET_ACTION_CHOICES,
    )
    target = models.ManyToManyField(Target)
    method = models.CharField(max_length=50)

    def __str__(self):
        return self.ipaddr
