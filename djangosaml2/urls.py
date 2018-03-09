"""Djangosaml2 Django URLs."""
from django.conf.urls import url

from djangosaml2 import views

app_name = 'djangosaml2'
urlpatterns = [
    url(r'^login/acs/$', views.acs, name='acs'),
    url(r'^signin/$', views.signin, name='signin'),
    url(r'^login/denied/$', views.denied, name='denied'),
]
