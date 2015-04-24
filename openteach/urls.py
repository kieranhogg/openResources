from django.conf.urls import patterns, include, url
from django.contrib import admin
from haystack.forms import SearchForm
from haystack.views import SearchView

urlpatterns = patterns('',
    (r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^search/$', SearchView(form_class=SearchForm)),
    url(r'', include('uploader.urls', namespace="uploader")),
    url(r'^uploader/', include('uploader.urls', namespace="uploader")),
    #(r'^taggit_autosuggest/', include('taggit_autosuggest.urls')),
)

