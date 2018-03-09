# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations, models

from api.models import Target


def create_groups_and_permissions(apps, schema_editor):
    """Create groups defined in config and add permissions to groups."""
    # Create Groups with Permissions
    # all access
    target_all_read = Permission.objects.get(codename='target_all_read')
    target_all_write = Permission.objects.get(codename='target_all_write')
    group, created = Group.objects.get_or_create(
        name=settings.GROUP_NAMES['ALL_READWRITE'])
    if created:
        group.permissions.add(target_all_read)
        group.permissions.add(target_all_write)

    # ipaddr access
    target_ipaddr_read = Permission.objects.get(codename='target_ipaddr_read')
    target_ipaddr_write = Permission.objects.get(codename='target_ipaddr_write')
    group, created = Group.objects.get_or_create(
        name=settings.GROUP_NAMES['IPADDR_READWRITE'])
    if created:
        group.permissions.add(target_ipaddr_read)
        group.permissions.add(target_ipaddr_write)

    # domain access
    target_domain_read = Permission.objects.get(codename='target_domain_read')
    target_domain_write = Permission.objects.get(codename='target_domain_write')
    group, created = Group.objects.get_or_create(
        name=settings.GROUP_NAMES['DOMAIN_READWRITE'])
    if created:
        group.permissions.add(target_domain_read)
        group.permissions.add(target_domain_write)

    # url access
    target_url_read = Permission.objects.get(codename='target_url_read')
    target_url_write = Permission.objects.get(codename='target_url_write')
    group, created = Group.objects.get_or_create(
        name=settings.GROUP_NAMES['URL_READWRITE'])
    if created:
        group.permissions.add(target_url_read)
        group.permissions.add(target_url_write)

    # hash access
    target_hash_read = Permission.objects.get(codename='target_hash_read')
    target_hash_write = Permission.objects.get(codename='target_hash_write')
    group, created = Group.objects.get_or_create(
        name=settings.GROUP_NAMES['HASH_READWRITE'])
    if created:
        group.permissions.add(target_hash_read)
        group.permissions.add(target_hash_write)

    # user access
    target_user_read = Permission.objects.get(codename='target_user_read')
    target_user_write = Permission.objects.get(codename='target_user_write')
    group, created = Group.objects.get_or_create(
        name=settings.GROUP_NAMES['USER_READWRITE'])
    if created:
        group.permissions.add(target_user_read)
        group.permissions.add(target_user_write)

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups_and_permissions),
    ]
