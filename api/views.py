"""API Django views."""
import logging

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
import netaddr
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer

from api.models import Target, TargetIpAddr
from api.serializers import TargetSerializer
from plugins.interfaces import TargetInterface
from banhammer.settings import GROUP_PERMISSIONS_ENABLED as group_perms_enabled

# get api logger
LOGGER = logging.getLogger(__name__)


class JSONResponse(HttpResponse):
    """Override JSONResponse to indent responses."""
    def __init__(self, data="", **kwargs):
        content = JSONRenderer().render(data, renderer_context={'indent': 4})
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


def get_user_permissions(user):
    """Get all permissions associated to user's groups."""
    if not group_perms_enabled:
        return ['target_all_read', 'target_all_write']
    groups = Group.objects.filter(user=user)
    permissions = []
    for grp in groups:
        permissions += [x.codename for x in grp.permissions.all()]
    return permissions


def get_all_targets(user):
    """Returns all targets user has permission to read."""
    permissions = get_user_permissions(user)
    if 'target_all_read' in permissions:
        return Target.objects.all()

    targets = Target.objects.none()
    if 'target_ipaddr_read' in permissions:
        targets = targets | Target.objects.filter(target_type=Target.IPADDR)
    if 'target_domain_read' in permissions:
        targets = targets | Target.objects.filter(target_type=Target.DOMAIN)
    if 'target_url_read' in permissions:
        targets = targets | Target.objects.filter(target_type=Target.URL)
    if 'target_hash_read' in permissions:
        targets = targets | Target.objects.filter(target_type=Target.HASH)
    if 'target_user_read' in permissions:
        targets = targets | Target.objects.filter(target_type=Target.USER)
    return targets


def permission_to_write(user, target_type):
    """Returns True if user has permission to write to this target type."""
    permissions = get_user_permissions(user)
    allow = False
    if 'target_all_write' in permissions:
        allow = True
    if target_type == Target.IPADDR and 'target_ipaddr_write' in permissions:
        allow = True
    if target_type == Target.DOMAIN and 'target_domain_write' in permissions:
        allow = True
    if target_type == Target.URL and 'target_url_write' in permissions:
        allow = True
    if target_type == Target.HASH and 'target_hash_write' in permissions:
        allow = True
    if target_type == Target.USER and 'target_user_write' in permissions:
        allow = True
    return allow


def permission_to_read(user, target_type):
    """Returns True if user has permission to read this target type."""
    permissions = get_user_permissions(user)
    allow = False
    if 'target_all_read' in permissions:
        allow = True
    if target_type == Target.IPADDR and 'target_ipaddr_read' in permissions:
        allow = True
    if target_type == Target.DOMAIN and 'target_domain_read' in permissions:
        allow = True
    if target_type == Target.URL and 'target_url_read' in permissions:
        allow = True
    if target_type == Target.HASH and 'target_hash_read' in permissions:
        allow = True
    if target_type == Target.USER and 'target_user_read' in permissions:
        allow = True
    return allow


def add_block(valid_data):
    """Perform blocking actions after adding to database."""
    if valid_data['target_action'] == Target.BAN:
        target = TargetInterface(
            valid_data['target'],
            valid_data['target_type'],
            valid_data['reason'],
        )
        target.run_method(valid_data['method'])


def add_to_targetipaddr_db(instance):
    """Adds IP addresses as individual entries in TargetIpAddr database."""
    if instance.target_type == Target.IPADDR:
        if '-' in instance.target:
            iprange = instance.target.split('-')
            iplist = list(netaddr.iter_iprange(iprange[0], iprange[1]))
        elif '/' in instance.target:
            iplist = list(netaddr.IPNetwork(instance.target))
        else:
            iplist = [instance.target]
        for ipaddr in iplist:
            try:
                # grab pre-existing entry
                ip_entry = TargetIpAddr.objects.get(
                    ipaddr=ipaddr,
                )
                if ip_entry.ipaddr_action != instance.target_action:
                    raise ValidationError({
                        'target': [
                            'Target "%s" is already marked for action "%s"' % (
                                ip_entry.ipaddr, ip_entry.ipaddr_action)
                        ]
                    })
            except TargetIpAddr.DoesNotExist:
                # create new entry
                ip_entry = TargetIpAddr(
                    ipaddr=ipaddr,
                    ipaddr_action=instance.target_action,
                    method=instance.method,
                )
                ip_entry.save()
            # associate IP address to target
            ip_entry.target.add(instance)


@transaction.atomic
def save_target(serializer):
    """Save Target."""
    # pre-save: Perform blocking actions
    add_block(serializer.validated_data)
    # save: create instance in Target database
    instance = serializer.save()
    # post-save: Add IP address entries to database
    add_to_targetipaddr_db(instance)


def remove_block(instance):
    """Perform unblocking actions before deleting from database."""
    if instance.target_action == Target.BAN:
        # TODO add deletion methods for plugins
        # target = TargetInterface(
        #     instance.target,
        #     instance.target_type,
        #     instance.reason,
        # )
        # target.run_method_delete(instance.method)
        pass


def delete_from_targetipaddr_db(instance):
    """Remove IP addresses from TargetIpAddr database."""
    if instance.target_type == Target.IPADDR:
        ip_addrs = instance.targetipaddr_set.all()
        for ip_addr in ip_addrs:
            # remove IP address if this Target is its only reference
            if ip_addr.target.count() == 1:
                ip_addr.delete()


def log_deletion(user, instance):
    """Log targets deleted from database."""
    msg = (
        'action="%s" user="%s" target="%s" target_action="%s" '
        'target_type="%s" reason="%s" method="%s"'
        % ("delete", user, instance.target, instance.target_action,
           instance.target_type, instance.reason, instance.method)
    )
    LOGGER.info(msg)


@transaction.atomic
def delete_target(user, instance):
    """Delete Target."""
    # pre-delete: Perform unblocking actions
    remove_block(instance)
    # pre-delete: Delete referenced IP's from TargetIpAddr database
    delete_from_targetipaddr_db(instance)
    # delete: remove instance from Target database
    instance.delete()
    # post-delete: Log targets removed from database
    log_deletion(user, instance)


@api_view(['GET', 'POST'])
def target_list(request):
    """List all targets or add a target."""
    if request.method == 'GET':
        targets = get_all_targets(request.user)
        serializer = TargetSerializer(targets, many=True)
        request.accepted_media_type = 'application/json; indent=4'
        return JSONResponse(serializer.data)

    if request.method == 'POST':
        # check user write permissions
        if not permission_to_write(request.user, request.data['target_type']):
            return JSONResponse(
                {'target_type': ['Insufficiant permissions.']},
                status=status.HTTP_403_FORBIDDEN)
        # serialize data
        serializer = TargetSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                save_target(serializer)
            except ValidationError as err:
                return JSONResponse(err, status=status.HTTP_400_BAD_REQUEST)
            return JSONResponse(serializer.data,
                                status=status.HTTP_201_CREATED)
        return JSONResponse(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def target_list_bytype(request, target_type):
    """List all targets by type."""
    if request.method == 'GET':
        # check user read permissions
        if not permission_to_read(request.user, target_type):
            return JSONResponse(
                {'target_type': ['Insufficiant permissions.']},
                status=status.HTTP_403_FORBIDDEN)
        targets = Target.objects.filter(target_type=target_type)
        serializer = TargetSerializer(targets, many=True)
        return JSONResponse(serializer.data)


@api_view(['GET', 'DELETE'])
def target_detail(request, target_id):
    """Retrieve a target."""
    try:
        target = Target.objects.get(id=target_id)
    except Target.DoesNotExist:
        return JSONResponse(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # check user read permissions
        if not permission_to_read(request.user, target.target_type):
            return JSONResponse(status=status.HTTP_404_NOT_FOUND)
        serializer = TargetSerializer(target)
        return JSONResponse(serializer.data)

    if request.method == 'DELETE':
        # check user write permissions
        if not permission_to_write(request.user, target.target_type):
            return JSONResponse(status=status.HTTP_404_NOT_FOUND)
        try:
            delete_target(request.user, target)
        except ValidationError as err:
            return JSONResponse(
                err, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return JSONResponse({}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def plugin_dict_bytype(request, target_type):
    """Get dictionary of plugins by type."""
    if request.method == 'GET':
        # check user read permissions
        if not permission_to_read(request.user, target_type):
            return JSONResponse(
                {'target_type': ['Insufficiant permissions.']},
                status=status.HTTP_403_FORBIDDEN)
        target = TargetInterface(None, target_type)
        return JSONResponse(target.plugins)


@api_view(['GET'])
def method_list_bytype(request, target_type):
    """Get list of methods by type."""
    if request.method == 'GET':
        # check user read permissions
        if not permission_to_read(request.user, target_type):
            return JSONResponse(
                {'target_type': ['Insufficiant permissions.']},
                status=status.HTTP_403_FORBIDDEN)
        target = TargetInterface(None, target_type)
        return JSONResponse(target.methods)
