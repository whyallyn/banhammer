"""Register API as Django app."""
from __future__ import unicode_literals

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """BanHammer API Django app."""
    name = 'api'

    def ready(self):
        import api.signals
