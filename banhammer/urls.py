"""banhammer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from banhammer.settings import SAML2_ENABLED

urlpatterns = [
    url(
        r'^favicon.ico$',
        RedirectView.as_view(
            url=staticfiles_storage.url('web/img/favicon.ico'),
            permanent=False),
        name="favicon"
    ),
    url(r'^web/', include('web.urls', namespace='web')),
    url(r'^api/v1/', include('api.urls', namespace='api')),
    url(r'^ebl/', include('ebl.urls', namespace='ebl')),
]

if SAML2_ENABLED:
    urlpatterns = [
        url(r'^saml2/', include('djangosaml2.urls', namespace='djangosaml2')),
    ] + urlpatterns
