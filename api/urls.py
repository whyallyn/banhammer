"""API Django URLs."""
from django.conf.urls import url

from api import views

app_name = 'api'
urlpatterns = [
    url(
        r'^targets/$',
        views.target_list,
        name='target_list',
    ),
    url(
        r'^targets/(?P<target_type>(ip|domain|url|hash|user))/$',
        views.target_list_bytype,
        name='target_list_bytype',
    ),
    url(
        r'^targets/(?P<target_id>.+)$',
        views.target_detail,
        name='target_detail',
    ),
    url(
        r'^plugins/(?P<target_type>(ip|domain|url|hash|user))/$',
        views.plugin_dict_bytype,
        name='plugin_dict_bytype',
    ),
    url(
        r'^methods/(?P<target_type>(ip|domain|url|hash|user))/$',
        views.method_list_bytype,
        name='method_list_bytype',
    ),
]
