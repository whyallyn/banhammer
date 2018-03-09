"""EBL Django URLs."""
from django.conf.urls import url

from ebl import views

app_name = 'ebl'
urlpatterns = [
    url(r'^(?P<target_type>(ip|domain|url))$',
        views.target_list_ebl, name='ebl'),
]
