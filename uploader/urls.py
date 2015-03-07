from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView

from uploader import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^lookup/syllabus/(?P<subject_id>\d+)/$', views.get_syllabuses, name='get_syllabuses'),
    url(r'^lookup/unit/(?P<syllabus_id>\d+)/$', views.get_units, name='get_units'),
    url(r'^lookup/unit_topic/(?P<unit_id>\d+)/$', views.get_unit_topics, name='get_unit_topics'),
    
    url(r'^resource/(?P<slug>[\w\d-]+)/$', views.view_resource, name='view_resource'),
    url(r'^resource/(?P<slug>[\w\d-]+)/delete$', views.delete_resource, name='delete_resource'),
    #url(r'^resource/(?P<slug>[\w\d-]+)/edit$', views.resource, name='resource'),
    
    url(r'^bookmark/add/$', views.bookmark, name='bookmark'),
    url(r'^bookmark/link/(?P<slug>[\w\d-]+)/$', views.link_bookmark, name='link_bookmark'),
    url(r'^bookmark/add/stage_two/$', views.link_resource, name='link_resource'),
    url(r'^bookmark/(?P<slug>[\w\d-]+)/edit/$', views.bookmark, name='bookmark'),
    url(r'^bookmark/(?P<slug>[\w\d-]+)/delete/$', views.delete_bookmark, name='delete_bookmark'),

    url(r'^file/add/$', views.file, name='file'),
    url(r'^file/add/stage_two/$', views.link_resource, name='link_resource'),
    url(r'^file/link/(?P<slug>[\w\d-]+)/$', views.link_file, name='link_file'),
    url(r'^file/(?P<slug>[\w\d-]+)/edit/$', views.file, name='file'),
    url(r'^file/(?P<slug>[\w\d-]+)/delete/$', views.delete_file, name='delete_file'),

    url(r'^profile/resources', views.user_resources, name='user_resources'),
    url(r'^profile/files', views.user_files, name='user_files'),
    url(r'^profile/bookmarks', views.user_bookmarks, name='user_bookmarks'),
    url(r'^profile/questions', views.user_questions, name='user_questions'),
    url(r'^profile/(?P<username>[\w\d-]+)/$', views.profile, name='profile'),
    
    url(r'^leaderboard', views.leaderboard, name='leaderboard'),
    
    url(r'^rate/(?P<resource_id>\d+)/(?P<rating>\d+)/$', views.rate, name='rate'),
    
    url(r'^licences', views.licences, name='licences'),
    
    url(r'^upload_image', views.upload_image, name='upload_image'),
    url(r'^image/(?P<image_id>\d+)/$', views.view_image, name='view_image'),
    
    url(r'^test/(?P<slug>[\w\d-]+)/feedback', views.test_feedback, name='test_feedback'),
    url(r'^test/(?P<slug>[\w\d-]+)', views.test, name='test'),
    url(r'^add-question/(?P<slug>[\w\d-]+)', views.question, name='question'),
    
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/$', views.syllabus, name='syllabus'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/resources/$', views.syllabus_resources, name='syllabus_resources'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/$', views.syllabuses, name='syllabuses'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/$', views.unit, name='unit'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/resources/$', views.unit_resources, name='unit_resources'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/$', views.unit_topic, name='unit_topic'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/notes/$', views.view_notes, name='view_notes'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/notes/edit/$', views.notes, name='notes'),
    url(r'^(?P<slug>[\w\d-]+)/$', views.subject, name='subject'),

    # static pages
    url(r'^about',
    TemplateView.as_view(template_name='uploader/about.html'),
    name='about'),
    url(r'^user_profile',
    TemplateView.as_view(template_name='uploader/profile.html'),
    name='profile'),
    url(r'^add-resource', 
    TemplateView.as_view(template_name='uploader/add_resource.html'),
    name='add_resource'),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)