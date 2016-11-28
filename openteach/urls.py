from django.conf.urls import patterns, include, url
from django.contrib import admin

from openteach import settings

#if not settings.DEBUG:
#from haystack.forms import HighlightedSearchForm
#from haystack.views import SearchView

urlpatterns = patterns('',
    #(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('allauth.urls')),
    url(r'', include('uploader.urls', namespace="uploader")),
    url(r'^uploader/', include('uploader.urls', namespace="uploader")),
)

#if not settings.DEBUG:
#additional_patterns = patterns(
#    url(r'^search/$', SearchView(form_class=HighlightedSearchForm)),
#)
#urlpatterns += additional_patterns 

additional_patterns = patterns(
    url(r'', include('uploader.urls', namespace="uploader")),
    url(r'^uploader/', include('uploader.urls', namespace="uploader")),
)

urlpatterns += additional_patterns
