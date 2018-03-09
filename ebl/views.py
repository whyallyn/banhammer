"""EBL Django views."""
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from api.models import Target, TargetIpAddr


@require_http_methods(['GET'])
def target_list_ebl(request, target_type):
    """List all targets by type."""
    if request.method == 'GET':
        ebl = ''
        if target_type == Target.IPADDR:
            ip_addrs = TargetIpAddr.objects.filter(
                ipaddr_action=Target.BAN)
            for ipa in ip_addrs:
                if 'paloaltonetworks_add_to_ebl' in ipa.method:
                    ebl += '%s\n' % ipa.ipaddr
        else:
            targets = Target.objects.filter(
                target_action=Target.BAN,
                target_type=target_type).distinct('target')
            for tgt in targets:
                if 'paloaltonetworks_add_to_ebl' in tgt.method:
                    ebl += '%s\n' % tgt.target
        return HttpResponse(ebl, content_type='text/plain')
