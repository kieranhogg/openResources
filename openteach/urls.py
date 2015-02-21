from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'openteach.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    url(r'^uploader/', include('uploader.urls', namespace="uploader")),
    url(r'^admin/', include(admin.site.urls)),
    #(r'^accounts/', include('registration.backends.simple.urls')),
    (r'^accounts/', include('allauth.urls')),
)
