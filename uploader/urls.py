from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView

from uploader import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'lookup/syllabus/(?P<subject_id>\d+)/$', views.get_syllabuses, name='get_syllabuses'),
    url(r'lookup/unit/(?P<syllabus_id>\d+)/$', views.get_units, name='get_units'),
    url(r'lookup/unit_topic/(?P<unit_id>\d+)/$', views.get_unit_topics, name='get_unit_topics'),
    
    url(r'subject/(?P<slug>[-\w]+)/$', views.subject, name='subject'),
    url(r'subject/(?P<subject_slug>[-\w]+)/(?P<exam_slug>[-\w]+)/$', views.syllabuses, name='syllabuses'),
    
    url(r'syllabus/(?P<slug>[-\w]+)/$', views.syllabus, name='syllabus'),
    url(r'syllabus/(?P<slug>[-\w]+)/resources/$', views.syllabus_resources, name='syllabus_resources'),
    
    url(r'resource/add/$', views.add_resource, name='add_resource'),
    
    url(r'bookmark/add/$', views.add_bookmark, name='add_bookmark'),
    url(r'bookmark/add/stage_two/$', views.add_resource_stage_two, name='add_resource_stage_two'),
    url(r'bookmark/link/(?P<slug>[-\w]+)/$', views.link_bookmark, name='link_bookmark'),

    url(r'file/add/$', views.add_file, name='add_file'),
    url(r'file/add/stage_two/$', views.add_resource_stage_two, name='add_resource_stage_two'),
    url(r'file/link/(?P<slug>[-\w]+)/$', views.link_file, name='link_file'),

    url(r'unit/(?P<slug>[-\w]+)/$', views.unit, name='unit'),
    url(r'unit/(?P<slug>[-\w]+)/resources/$', views.unit_resources, name='unit_resources'),
    url(r'unit_topic/(?P<slug>[-\w]+)/$', views.unit_topic, name='unit_topic'),
    url(r'unit_topic/(?P<slug>[-\w]+)/notes/$', views.view_notes, name='view_notes'),
    url(r'unit_topic/(?P<slug>[-\w]+)/notes/edit/$', views.notes, name='notes'),

    url(r'resource/(?P<slug>[-\w]+)/$', views.resource, name='resource'),

    url(r'profile/resources/$', views.user_resources, name='user_resources'),
    url(r'profile/(?P<username>[-\w]+)/$', views.profile, name='profile'),
    
    url(r'leaderboard/$', views.leaderboard, name='leaderboard'),
    
    url(r'rate/(?P<resource_id>\d+)/(?P<rating>\d+)/$', views.rate, name='rate'),
    
    url(r'licences/$', views.licences, name='licences'),
    
    url(r'upload_image/$', views.upload_image, name='upload_image'),
    url(r'image/(?P<image_id>\d+)/$', views.view_image, name='view_image'),
    
    # static pages
    url(r'^about',
    TemplateView.as_view(template_name='uploader/about.html'),
    name='about'),
    url(r'^user_profile',
    TemplateView.as_view(template_name='uploader/profile.html'),
    name='profile'),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)