"""Web Django URLs."""
from django.conf.urls import url

from web import views

app_name = 'web'
urlpatterns = [
    url(r'^$', views.ban, name='index'),
    url(r'^ban$', views.ban, name='ban'),
    url(r'^allow$', views.allow, name='allow'),
    url(r'^list$', views.blist, name='list'),
    url(r'^docs$', views.docs, name='docs'),
    url(r'^signout$', views.signout, name='signout'),
]
