from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView

from uploader import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'subject/(?P<subject_id>\d+)/$', views.subject, name='subject'),
    url(r'subject/(?P<subject_id>\d+)/(?P<slug>[-\w]+)/$', views.subject, name='subject'),
    url(r'subject/(?P<subject_id>\d+)/exam_level/(?P<exam_level_id>\d+)/$', views.syllabuses, name='syllabuses'),
    url(r'subject/(?P<subject_id>\d+)/(?P<slug>[-\w]+)/exam_level/(?P<exam_level_id>\d+)/(?P<slug2>[-\w]+)/$', views.syllabuses, name='syllabuses'),
    url(r'syllabus/(?P<syllabus_id>\d+)/$', views.syllabus, name='syllabus'),
    url(r'syllabus/(?P<syllabus_id>\d+)/(?P<slug>[-\w]+)/$', views.syllabus, name='syllabus'),
    url(r'resource/add/$', views.add_resource, name='add_resource'),
    url(r'bookmark/add/$', views.add_bookmark, name='add_bookmark'),
    url(r'file/add/$', views.add_file, name='add_file'),
    url(r'bookmark/add/stage_two/$', views.add_resource_stage_two, name='add_resource_stage_two'),
    url(r'file/add/stage_two/$', views.add_resource_stage_two, name='add_resource_stage_two'),
    url(r'unit/(?P<unit_id>\d+)/$', views.unit, name='unit'),
    url(r'unit/(?P<unit_id>\d+)/(?P<slug>[-\w]+)/$', views.unit, name='unit'),
    url(r'unit_topic/(?P<unit_topic_id>\d+)/$', views.unit_topic, name='unit_topic'),
    url(r'unit_topic/(?P<unit_topic_id>\d+)/(?P<slug>[-\w]+)/$', views.unit_topic, name='unit_topic'),
    url(r'resource/(?P<resource_id>\d+)/(?P<slug>[-\w]+)/$', views.resource, name='resource'),
    url(r'resource/(?P<resource_id>\d+)/$', views.resource, name='resource'),
    url(r'profile/$', views.profile, name='profile'),
    url(r'profile/(?P<user_id>\d+)/$', views.profile, name='profile'),
    
    # static pages
    url(r'^about',
    TemplateView.as_view(template_name='uploader/about.html'),
    name='about'),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)