from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'', include('uploader.urls', namespace="uploader")),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^uploader/', include('uploader.urls', namespace="uploader")),
    url(r'^accounts/', include('allauth.urls')),
)

