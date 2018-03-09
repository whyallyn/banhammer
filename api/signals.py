"""API Django signals."""
import logging

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from api.models import Target

# get api logger
LOGGER = logging.getLogger(__name__)


@receiver(pre_save, sender=Target)
def limit_block_entries(sender, instance, **kwargs):
    """Limit IP, Domain, and URL blocks to 10K entries."""
    limit = 10000
    limited_types = {Target.IPADDR, Target.DOMAIN, Target.URL}
    if (instance.target_action == Target.BAN and
            instance.target_type in limited_types and
            Target.objects.filter(
                target_action=Target.BAN,
                target_type=instance.target_type).count() >= limit):
        # count has exceeded limit
        raise ValidationError(
            {'target': 'Exceeded %s %s instances.' % (limit, Target.BAN)})


@receiver(post_save, sender=Target)
def log_creation(sender, instance, created, **kwargs):
    """Log targets added to database."""
    if created:
        msg = (
            'action="%s" user="%s" target="%s" target_action="%s" '
            'target_type="%s" reason="%s" method="%s"'
            % (
                "create",
                instance.user,
                instance.target,
                instance.target_action,
                instance.target_type,
                instance.reason,
                instance.method,
            )
        )
        LOGGER.info(msg)
