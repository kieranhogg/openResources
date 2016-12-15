from django.conf.urls import include, url
from django.contrib import admin

from openteach import settings
from uploader import views

#if not settings.DEBUG:
#from haystack.forms import HighlightedSearchForm
#from haystack.views import SearchView

urlpatterns = [
	#url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^', include('uploader.urls', namespace="uploader")),
    #url(r'^uploader/', include('uploader.urls', namespace="uploader")),
    #url(r'^$', views.index, name='index'),
]

#if not settings.DEBUG:
#additional_patterns = patterns(
#    url(r'^search/$', SearchView(form_class=HighlightedSearchForm)),
#)
#urlpatterns += additional_patterns 

