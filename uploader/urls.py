from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic.base import TemplateView

from uploader import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^denied/$', views.denied, name='denied'),
    
    url(r'^assignment/add/$', views.assignment, name='assignment'),
    url(r'^assignment/(?P<code>[\w\d]+)/$', views.view_assignment, name='view_assignment'),
    url(r'^assignment/(?P<code>[\w\d]+)/edit/$', views.assignment, name='assignment'),
    url(r'^assignment/(?P<code>[\w\d]+)/delete/$', views.delete_assignment, name='delete_assignment'),
    url(r'^assignment/(?P<assignment_code>[\w\d-]+)/mark/(?P<submission_id>[\d]+)/$', views.mark_assignment, name='mark_assignment'),
    url(r'^assignment/(?P<assignment_code>[\w\d-]+)/mark/(?P<absent>[\w]+)/(?P<student_id>[\d]+)', views.mark_assignment, name='mark_assignment'),
    
    url(r'^lookup/syllabus/(?P<subject_id>\d+)/$', views.get_syllabuses, name='get_syllabuses'),
    url(r'^lookup/unit/(?P<syllabus_id>\d+)/$', views.get_units, name='get_units'),
    url(r'^lookup/quick/(?P<type>[\w]+)/(?P<code>[\w\d]+)/$', views.get_object_from_code, name='get_object_from_code'),
    url(r'^lookup/unit_topic/(?P<unit_id>\d+)/$', views.get_unit_topics, name='get_unit_topics'),
    url(r'^lookup/url_description/(?P<url>.+)$', views.get_url_description, name='get_url_description'),
    url(r'^bulk/bookmark/(?P<action>.+)/(?P<ids>.+)/$', views.bulk_bookmark_update, name='bulk_bookmark_update'),
    url(r'^pre-post/(?P<action>.+)/(?P<id>.+)/$', views.pre_post, name='pre_post'),
    
    url(r'^subjects/$', views.subjects, name='subjects'),
    url(r'^favourites/$', views.favourites, name='favourites'),
    url(r'^favourites/add-(?P<thing>[\w\d-]+)/(?P<slug>[\w\d-]+)$', views.add_favourite, name='add_favourite'),
    url(r'^favourites/remove-(?P<thing>[\w\d-]+)/(?P<slug>[\w\d-]+)$', views.remove_favourite, name='remove_favourite'),
    
    url(r'^resource/(?P<slug>[\w\d-]+)/$', views.view_resource, name='view_resource'),
    url(r'^resource/(?P<slug>[\w\d-]+)/embed/$', views.view_resource_embed, name='view_resource_embed'),
    url(r'^resource/(?P<slug>[\w\d-]+)/delete$', views.delete_resource, name='delete_resource'),
    url(r'^lesson/(?P<code>[\w\d-]+)/edit', views.edit_lesson, name='edit_lesson'),
    url(r'^lesson/(?P<code>[\w\d-]+)/delete', views.delete_lesson, name='delete_lesson'),
    url(r'^lesson/(?P<code>[\w\d-]+)/link', views.link_lesson, name='link_lesson'),
    url(r'^lesson/new/$', views.lesson_creator, name='lesson_creator'),
    url(r'^lesson_item/(?P<id>[\d-]+)/edit', views.edit_lesson_item, name='edit_lesson_item'),
    #url(r'^resource/(?P<slug>[\w\d-]+)/edit$', views.resource, name='resource'),
    
    url(r'^groups/$', views.groups_list, name='groups_list'),
    url(r'^groups/add/$', views.groups, name='groups'),
    url(r'^groups/(?P<slug>[\w\d-]+)/edit/$', views.groups, name='groups'),
    url(r'^group/(?P<slug>[\w\d-]+)/lesson/(?P<code>[\w\d-]+)/$', views.lesson, name='lesson'),
    url(r'^group/(?P<code>[\w\d-]+)/$', views.group, name='group'),
    url(r'^group/(?P<group_code>[\w\d-]+)/lesson/(?P<code>[\w\d-]+)/show/$', views.lesson_show, name='lesson_show'),
    url(r'^group/(?P<group_code>[\w\d-]+)/lesson/(?P<code>[\w\d-]+)/present/$', views.lesson_present, name='lesson_present'),
    
    # url(r'^bookmark/add/(?P<url>[-_./\w\d-]+)$', views.bookmark, name='bookmark'),
    url(r'^bookmark/add/', views.bookmark, name='bookmark'),
    url(r'^bookmark/link/(?P<slug>[\w\d-]+)/$', views.link_bookmark, name='link_bookmark'),
    # url(r'^bookmark/add/stage_two/$', views.link_resource, name='link_resource'),
    url(r'^bookmark/(?P<slug>[\w\d-]+)/edit/$', views.bookmark, name='bookmark'),
    url(r'^bookmark/(?P<slug>[\w\d-]+)/delete/$', views.delete_bookmark, name='delete_bookmark'),

    url(r'^file/add/$', views.file, name='file'),
    url(r'^file/add/stage_two/$', views.link_resource, name='link_resource'),
    url(r'^file/link/(?P<slug>[\w\d-]+)/$', views.link_file, name='link_file'),
    url(r'^file/(?P<slug>[\w\d-]+)/edit/$', views.file, name='file'),
    url(r'^file/(?P<slug>[\w\d-]+)/delete/$', views.delete_file, name='delete_file'),
    
    url(r'^user/profile/$', views.profile, name='profile'),
    url(r'^user/resources', views.user_resources, name='user_resources'),
    url(r'^user/files', views.user_files, name='user_files'),
    url(r'^user/bookmarks', views.user_bookmarks, name='user_bookmarks'),
    url(r'^user/questions', views.user_questions, name='user_questions'),
    url(r'^user/lessons', views.user_lessons, name='user_lessons'),
    url(r'^user/grading/add/', views.grading, name='grading'),
    url(r'^user/grading/', views.user_grading, name='user_grading'),
    url(r'^user/tests/', views.user_tests, name='user_tests'),
    url(r'^user/(?P<username>[\w\d-]+)/$', views.profile, name='profile'),
    
    url(r'lesson/(?P<slug>[\w\d-]+)/$', views.lesson, name='lesson'),

    
    url(r'^notes/(?P<code>[\w\d-]+)/$', views.view_notes_code, name='view_notes_code'),
    # url(r'^notes/(?P<slug>[\w\d-]+)/edit/$', views.notes_d, name='notes_d'),
    
    url(r'^students/signup/$', views.student_signup, name='student_signup'),
    url(r'^teachers/signup/$', views.teacher_signup, name='teacher_signup'),

    
    # url(r'^leaderboard', views.leaderboard, name='leaderboard'),
    
    url(r'^vote/(?P<content_type>[\w]+)/(?P<object_id>[\d]+)/(?P<vote>[\d])/$', views.vote, name='vote'),
    
    url(r'^licences', views.licences, name='licences'),
    
    url(r'^upload_image', views.upload_image, name='upload_image'),
    url(r'^image/(?P<image_id>\d+)/$', views.view_image, name='view_image'),
    
    url(r'^test/add', views.add_test, name='add_test'),
    url(r'^test/(?P<code>[\w\d-]+)/feedback', views.test_feedback, name='test_feedback'),
    url(r'^test/(?P<code>[\w\d-]+)/link', views.link_test, name='link_test'),
    url(r'^test/(?P<code>[\w\d-]+)', views.test, name='test'),

    
    url(r'^add-question/(?P<slug>[\w\d-]+)', views.question, name='question'),
    
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/$', views.syllabus, name='syllabus'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/resources/$', views.syllabus_resources, name='syllabus_resources'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/$', views.syllabuses, name='syllabuses'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/$', views.unit, name='unit'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/resources/$', views.unit_resources, name='unit_resources'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/resources/$', views.unit_topic_resources, name='unit_topic_resources'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/notes/$', views.view_notes, name='view_notes'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/lessons/$', views.unit_topic_lessons, name='unit_topic_lessons'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/notes/edit/$', views.notes, name='notes'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/questions/$', views.questions, name='questions'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/questions/add/$', views.question, name='question'),
    url(r'^(?P<subject_slug>[\w\d-]+)/(?P<exam_slug>[\w\d-]+)/(?P<syllabus_slug>[\w\d-]+)/(?P<unit_slug>[\w\d-]+)/(?P<slug>[\w\d-]+)/$', views.unit_topic, name='unit_topic'),
    url(r'^(?P<slug>[\w\d-]+)/$', views.subject, name='subject'),

    # static pages
    url(r'^about',
    TemplateView.as_view(template_name='uploader/about.html'),
    name='about'),
    url(r'^add-resource', 
    TemplateView.as_view(template_name='uploader/add_resource.html'),
    name='add_resource'),
    url(r'^signup',
    TemplateView.as_view(template_name='uploader/signup.html'),
    name='signup'),

) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)