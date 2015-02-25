from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'openteach.views.home', name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('uploader.urls', namespace="uploader")),
    url(r'^uploader/', include('uploader.urls', namespace="uploader")),
    url(r'^accounts/', include('allauth.urls')),

)