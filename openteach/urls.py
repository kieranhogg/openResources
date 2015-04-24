from django.conf.urls import patterns, include, url
from django.contrib import admin
#from haystack.generic_views.SearchView
#from haystack.forms import HighlightedSearchForm

urlpatterns = patterns('',
    (r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^search/', include('haystack.urls')),
    url(r'', include('uploader.urls', namespace="uploader")),
    url(r'^uploader/', include('uploader.urls', namespace="uploader")),
    #(r'^taggit_autosuggest/', include('taggit_autosuggest.urls')),
)

