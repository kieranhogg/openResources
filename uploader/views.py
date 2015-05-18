from __future__ import division

import re
import requests
import logging
import json
import time
import urllib2
import mimetypes
import datetime
import diff_match_patch

from django.apps import apps
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.files import File as DjangoFile
from django.core.files.temp import NamedTemporaryFile
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import user_passes_test, permission_required
from django.db import IntegrityError
from django.db.models import Avg
from django.http import (HttpResponse, HttpResponseRedirect, JsonResponse,
                         Http404, HttpResponseForbidden)
from django.shortcuts import (render, get_object_or_404, get_list_or_404,
                              render_to_response, redirect)
from django.template import Context, loader, RequestContext
from django.utils import timezone

from boxview import boxview

from uploader.models import *
from uploader.forms import *
from uploader.decorators import is_teacher, is_student
from uploader.utils import *

logging.basicConfig()
logger = logging.getLogger(__name__)

def index(request):
    """Homepage view depending on logged in and user type
    """
    if not request.user.is_authenticated():

        subjects = Subject.objects.filter(active=1)

        # # get messages TODO use constants
        # user_messages = Message.objects.filter(user_to=request.user.id)
        # announce_messages = Message.objects.filter(type=2)
        # sticky_messages = Message.objects.filter(type=3)

        context = {
            'subjects': subjects,
            # 'user_messages': user_messages | announce_messages | sticky_messages,
            'homepage': True
        }
        return render(request, 'uploader/index.html', context)
    else:
        if hasattr(request.user, 'teacherprofile'):
            groups = Group.objects.filter(teacher=request.user)
            
            tests = Test.objects.filter(group__in=groups)[:5]
            lessons = GroupLesson.objects.filter(set_by=request.user).order_by('-date', '-pub_date')[:5]
            assignments = Assignment.objects.filter(group__in=groups).order_by('-deadline', '-pub_date')[:5]
            
            #FIXME templatetag these
            for lesson in lessons:
                lesson.link = shorten_lesson_url(request, lesson.group.code, lesson.lesson.code)
                lesson.feedback = LessonPrePostResponse.objects.filter(type='post', pre_post__group_lesson=lesson).aggregate(Avg('score'))['score__avg']

            context = {'groups': groups, 'tests': tests, 'lessons': lessons, 'assignments': assignments}
            return render(request, 'uploader/teacher_home.html', context)
        else:
            groups = StudentGroup.objects.filter(student=request.user)
            # assignments = Assignment.objects.filter(group__in=groups)
            submissions = AssignmentSubmission.objects.filter(student=request.user).distinct('assignment').order_by('assignment', '-submitted')

            # assignments.assignmentsubmission_set.filter(student=request.user)
            lessons = GroupLesson.objects.filter(group__in=groups)
            tests = Test.objects.filter(group__in=groups)
            
            context = {
                'tests': tests, 
                'assignments': submissions, 
                'tests': tests
            }
    
            return render(
                request, 'uploader/student_home.html', context)


def subjects(request):
    """
    Shows a list of all subjects that are active for the resources page
    """
    subjects = Subject.objects.filter(active=1)
    return render(request, 'uploader/subjects.html', {'subjects': subjects})


@login_required
def favourites(request):
    """
    Shows a list of the current user's favourite items
    """
    subjects = get_user_profile(request.user).subjects.all()
    syllabuses = SyllabusFavourite.objects.filter(user=request.user)
    units = UnitFavourite.objects.filter(user=request.user)
    unit_topics = UnitTopicFavourite.objects.filter(user=request.user)

    context = {'subjects': subjects, 'syllabuses': syllabuses, 'units': units,
               'unit_topics': unit_topics}

    return render(request, 'uploader/favourites.html', context)


@login_required
def add_favourite(request, slug, thing):
    """ Adds items to favourites
    """
    if thing == 'syllabus':
        s = get_object_or_404(Syllabus, slug=slug)
        try:
            sf = SyllabusFavourite(user=request.user, syllabus=s)
            sf.save()
        except IntegrityError:
            messages.error(request, "Already in favourites")

    elif thing == 'unit':
        u = get_object_or_404(Unit, slug=slug)
        try:
            uf = UnitFavourite(user=request.user, unit=u)
            uf.save()
        except IntegrityError:
            messages.error(request, "Already in favourites")

    elif thing == 'unit_topic':
        ut = get_object_or_404(UnitTopic, slug=slug)
        try:
            utf = UnitTopicFavourite(user=request.user, unit_topic=ut)
            utf.save()
        except IntegrityError:
            messages.error(request, "Already in favourites")

    messages.success(request, "Added to favourites")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def remove_favourite(request, slug, thing):
    """ Removes items to favourites
    """
    if thing == 'syllabus':
        s = get_object_or_404(Syllabus, slug=slug)
        sf = SyllabusFavourite.objects.get(user=request.user, syllabus=s)
        sf.delete()
    elif thing == 'unit':
        u = get_object_or_404(Unit, slug=slug)
        uf = UnitFavourite.objects.get(user=request.user, unit=u)
        uf.delete()
    elif thing == 'unit_topic':
        ut = get_object_or_404(UnitTopic, slug=slug)
        utf = UnitTopicFavourite.objects.get(user=request.user, unit_topic=ut)
        utf.delete()

    messages.success(request, "Removed from favourites")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def subject(request, slug):
    """View one subject, shows exam levels, e.g. GCSE
    """
    subject = get_object_or_404(Subject, slug=slug)

    # Sort by country first to enable grouping
    exam_levels = ExamLevel.objects.order_by('country', 'level_number')

    context = {'exam_levels': exam_levels, 'subject': subject}
    return render(request, 'uploader/subject_view.html', context)


def syllabus_resources(request, subject_slug, exam_slug, slug):
    """ Shows the resources with only a syllabus set
    """
    items = hierachy_from_slugs(subject_slug, exam_slug, slug)
    syllabus = items['syllabus']
    
    resources = Resource.objects.filter(
        syllabus__id=syllabus.id,
        unit__isnull=True,
        unit_topic__isnull=True)
        
    # rating is a function so we can't sort by it naturally
    resources = sorted(resources, None, key=lambda a: a.rating, reverse=True)

    context = {'syllabus': syllabus, 'resources': resources}
    return render(request, 'uploader/syllabus_resources.html', context)


def unit_topic(
        request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, unit_slug, slug)
    unit_topic = items['unit_topic']
    
    resources = Resource.objects.filter(unit_topic=unit_topic).count()
    notes = Note.objects.filter(unit_topic=unit_topic).count()
    question = MultipleChoiceQuestion.objects.filter(unit_topic=unit_topic)
    questions = question.count()
    lessons = Lesson.objects.filter(unit_topic=unit_topic, public=True)
    lessons = lessons.count()
    related = (UnitTopicLink.objects.filter(unit_topic_1=unit_topic) |
               UnitTopicLink.objects.filter(unit_topic_2=unit_topic))

    favourite = False
    if request.user.is_authenticated():
        try:
            favourite = UnitTopicFavourite.objects.get(
                unit_topic=unit_topic,
                user=request.user)
        except ObjectDoesNotExist as TypeError:
            pass

    context = {'unit_topic': unit_topic, 'resources': resources,
               'questions': questions, 'notes': notes,
               'related_topics': related, 'favourite': favourite,
               'lessons': lessons}
    return render(request, 'uploader/unit_topic.html', context)


def unit_topic_resources(
        request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    """Fetches related resources for a unit topic
    """
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, unit_slug, slug)
    unit_topic = items['unit_topic']
    resources = Resource.objects.filter(unit_topic=unit_topic)
    
    # rating is a function so we can't sort by it naturally
    resources = sorted(resources, None, key=lambda a: a.rating, reverse=True)

    context = {'unit_topic': unit_topic, 'resources': resources}
    return render(request, 'uploader/unit_topic_resources.html', context)
    
    
def unit_topic_lessons(request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    """Finds the publuc lessons for a particular unit topic
    """
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, unit_slug, slug)
    unit_topic = items['unit_topic']
    lessons = Lesson.objects.filter(unit_topic=unit_topic, public=True)
    
    return render(request, 'uploader/unit_topic_lessons.html', 
        {'lessons': lessons, 'unit_topic': unit_topic})

def unit_resources(request, subject_slug, exam_slug, syllabus_slug, unit_slug):
    """Finds the resources for a unit
    """
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, unit_slug)
    unit = items['unit']

    resources = Resource.objects.filter(
        unit__id=unit.id,
        unit_topic__isnull=True)
        
    # rating is a function so we can't sort by it naturally
    resources = sorted(resources, None, key=lambda a: a.rating, reverse=True)

    context = {'unit': unit, 'resources': resources}
    return render(request, 'uploader/unit_resources.html', context)


def syllabuses(request, subject_slug, exam_slug):
    """View list of syllabuses for a subject and level,
    e.g. {AQA, OCR} GCSE Maths
    """
    items = hierachy_from_slugs(subject_slug, exam_slug)
    subject = items['subject']
    level = items['exam_level']

    syllabus_list = Syllabus.objects.filter(
        subject=subject,
        exam_level=level,
    )

    context = {
        'syllabus_list': syllabus_list,
        'subject': subject,
        'level': level
    }
    return render(request, 'uploader/syllabus_index.html', context)


def syllabus(request, subject_slug, exam_slug, slug):
    """Show one syllabuses page, has units on
    """
    items = hierachy_from_slugs(subject_slug, exam_slug, slug)
    syllabus = items['syllabus']
    syllabus.description = render_markdown(syllabus.description)
    units = Unit.objects.filter(syllabus=syllabus).order_by('order', 'title')
    
    resources = Resource.objects.filter(
        syllabus__id=syllabus.id,
        unit__isnull=True,
        unit_topic__isnull=True).count()

    favourite = False
    if request.user.is_authenticated():
        try:
            favourite = SyllabusFavourite.objects.get(
                syllabus=syllabus,
                user=request.user)
        except ObjectDoesNotExist:
            pass

    context = {
        'syllabus': syllabus, 'units': units, 'favourite': favourite,
        'resources': resources
    }
    return render(request, 'uploader/syllabus.html', context)


def unit(request, subject_slug, exam_slug, syllabus_slug, slug):
    """A single unit view
    """
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, slug)
    syllabus = items['syllabus']
    unit = items['unit']
    unit_topics = UnitTopic.objects.filter(unit__id=unit.id).order_by(
        'section', 'pub_date')
    for unit_topic in unit_topics:
        if unit_topic.section_description:
            unit_topic.section_description = render_markdown(
                unit_topic.section_description)

    favourite = False
    if request.user.is_authenticated():
        try:
            favourite = UnitFavourite.objects.get(unit=unit, user=request.user)
        except ObjectDoesNotExist as TypeError:
            pass

    resources = Resource.objects.filter(unit__id=unit.id, unit_topic=None)

    context = {
        'resources': resources,
        'unit': unit,
        'unit_topics': unit_topics,
        'favourite': favourite
    }
    return render(request, 'uploader/unit.html', context)


def view_resource(request, slug, embed=False):
    """A single resource view
    """
    resource = get_object_or_404(Resource, slug=slug)
    if embed:
        template = 'uploader/resource_view_embed.html'
    else:
        template = 'uploader/resource_view.html'

    context = {'resource': resource}
    
    # Get the file preview from box
    if resource.file:
        if 'image' in resource.file.mimetype:
            resource.file.image = True
        elif resource.file.mimetype in settings.PREVIEW_CONTENT_TYPES:
            try:
                api = boxview.BoxView(settings.BOX_VIEW_KEY)
                file = str(settings.MEDIA_URL + resource.file.filename)
                doc = api.create_document(url=resource.file.file.url)

                doc_id = doc['id']

                count = 0
                success = True
                while True:
                    if not bool(api.ready_to_view(doc_id)):
                        if count == 5:
                            success = False
                            break
                        else:
                            time.sleep(0.5)
                            count += 0.5
                    else:
                        break

                if success:
                    session = api.create_session(doc_id, duration=300)
                    context['ses_id'] = session['id']
            except:
                # so many things to go wrong here, silently bail if it does, users
                # can still download the file
                pass

    return render(request, template, context)


def view_resource_embed(request, slug):
    return view_resource(request, slug, True)


@login_required
def delete_resource(request, slug):
    resource = get_object_or_404(Resource, slug=slug)
    if request.user == resource.uploader:
        resource.delete()
        messages.success(request, 'Resource unlinked')
        return HttpResponseRedirect(reverse('uploader:user_resources'))
    else:
        return HttpResponseForbidden("Permission denied")


@login_required
def delete_file(request, slug):
    file = get_object_or_404(File, slug=slug)
    if request.user == file.uploader:
        file.delete()
        messages.success(request, 'File deleted')
        return HttpResponseRedirect(reverse('uploader:user_files'))
    else:
        return HttpResponseForbidden("Permission denied")


@login_required
def delete_bookmark(request, slug):
    bookmark = get_object_or_404(Bookmark, slug=slug)
    if request.user == bookmark.uploader:
        bookmark.delete()
        messages.success(request, 'Bookmark deleted')
        return HttpResponseRedirect(reverse('uploader:user_bookmarks'))
    else:
        return HttpResponseForbidden("Permission denied")


def file(request, slug=None):
    if slug:
        file = get_object_or_404(File, slug=slug)

        if file.uploader != request.user and not request.user.is_superuser():
            return HttpResponseForbidden("No stairway, denied!")
    else:
        if request.user.is_authenticated():
            file = File(uploader=request.user)
        else:
            file = File()

    if request.POST:
        form = FileForm(request.POST, request.FILES or None, instance=file)
        if form.is_valid():
            if not slug:
                # new record
                file = form.save(commit=False)

                # if we are fetching from a URL
                mimetype = None

                if request.POST['url']:
                    url = request.POST['url']
                    filename = url.split('/')[-1]
                    file_temp = NamedTemporaryFile(delete=True)
                    file_temp.write(urllib2.urlopen(url).read())
                    file_temp.flush()
                    file.file.save(filename, DjangoFile(file_temp), save=False)
                    file.filename = filename

                    mimetype, encoding = mimetypes.guess_type(url)
                    the_file = file.file
                else:
                    the_file = request.FILES['file']
                    file.filename = the_file.name

                # set excluded fields
                file.filesize = the_file.size

                if mimetype:
                    file.mimetype = mimetype
                else:
                    file.mimetype = the_file.content_type

                if request.user.is_authenticated():
                    file.uploader = request.user
                else:
                    try:
                        to = settings.NEW_ACCOUNT_EMAIL
                        message = "An anonymous file was uploaded. \n\n"
                        message += "Title: " + file.title + "\n"
                        message += "Filename: " + file.filename + "\n"
                        message += "Filesize: " + filesizeformat(file.filesize)

                        send_mail('New File', message, 'no_reply@eduresourc.es',
                                  to, fail_silently=True)

                    except AttributeError:  # no NEW_ACCOUNT_EMAIL setting
                        pass

                file.slug = safe_slugify(file.title, File)

                form.save()
                form.save_m2m()
                return HttpResponseRedirect(
                    reverse('uploader:link_file', args=[file.slug]))
            else:
                form.save()
                return HttpResponseRedirect(reverse('uploader:user_files'))
    else:
        form = FileForm(instance=file)

    return render(
        request, 'uploader/add_file.html', {'form': form, 'media': form.media})


def bookmark(request, slug=None, url=None):
    bookmark = None

    if slug:
        bookmark = get_object_or_404(Bookmark, slug=slug)
        if bookmark.uploader != request.user and not request.user.is_superuser():
            return HttpResponseForbidden("No stairway, denied!")
    else:
        if request.user.is_authenticated():
            bookmark = Bookmark(uploader=request.user, link=url or None)
        else:
            bookmark = Bookmark(link=url or None)

    if request.POST:
        form = BookmarkForm(request.POST, instance=bookmark)

        if form.is_valid():
            if not slug:
                # insert
                bookmark = form.save(commit=False)
                bookmark.screenshot = get_screenshot(bookmark.link)
                bookmark.slug = safe_slugify(bookmark.title, Bookmark)
                form.save()

                if not request.user.is_authenticated():
                    try:
                        to = settings.NEW_ACCOUNT_EMAIL
                        message = "An anonymous bookmark was added. \n\n"
                        message += "Title: " + bookmark.title + " "
                        message += "URL: " + bookmark.url

                        send_mail('New Bookmark', message, 'no_reply@eduresourc.es',
                                  to, fail_silently=True)

                    except AttributeError:  # no NEW_ACCOUNT_EMAIL setting
                        pass

                form.save()

                return HttpResponseRedirect(
                    reverse('uploader:link_bookmark', args=[bookmark.slug]))
            else:
                form.save()
                return HttpResponseRedirect(reverse('uploader:user_bookmarks'))

    else:
        form = BookmarkForm(instance=bookmark)

    return render_to_response('uploader/add_bookmark.html', {
        'form': form,
    }, context_instance=RequestContext(request))


def link_file(request, slug):
    file = get_object_or_404(File, slug=slug)
    return link_resource(request, 'file', file)


def link_bookmark(request, slug):
    bookmark = get_object_or_404(Bookmark, slug=slug)
    return link_resource(request, 'bookmark', bookmark)


def link_lesson(request, code):
    lesson = get_object_or_404(Lesson, code=code)
    return link_resource(request, 'lesson', lesson)

# FIXME this could do with cleaning up and just using an HTML snippet
def link_resource(request, type, obj):
    bookmark = None
    file = None
    test = None

    if type == 'bookmark':
        bookmark = obj
    elif type == 'file':
        file = obj
    elif type == 'test':
        test = obj
    elif type == 'lesson':
        lesson = obj

    if type == 'bookmark' or type == 'file':
        if request.user.is_authenticated():
            resource = Resource(uploader=request.user, file=file or None,
                                bookmark=bookmark or None, approved=False)
        else:
            resource = Resource(file=file or None,
                                bookmark=bookmark or None, approved=False)

    if request.method == 'POST' and 'save' in request.POST:
        if type == 'bookmark' or type == 'file':
            form = LinkResourceForm(request.POST, instance=resource)
            if form.is_valid():
                resource = form.save(commit=False)
                resource.code = generate_code(Resource)
                # work out slug
                if resource.file is not None:
                    resource.slug = safe_slugify(resource.file.slug, Resource)
                else:
                    resource.slug = safe_slugify(resource.bookmark.slug, Resource)

                if request.user.is_authenticated():
                    # if we're logged in auto-approve
                    resource.approved = True
                    score_points(request.user, "Add Resource")
                form.save()

                messages.success(request, 'Resource added, thank you!')
                return redirect(reverse('uploader:index'))
        elif type == 'test':
            test.subject = Subject.objects.get(pk=request.POST['subject'])
            test.syllabus = Syllabus.objects.get(pk=request.POST['syllabus'])
            test.unit = Unit.objects.get(pk=request.POST.get('unit'))
            test.unit_topic = UnitTopic.objects.get(
                pk=request.POST.get('unit_topic'))
            test.save()
            
            return redirect(reverse('uploader:user_tests'))
        elif type == 'lesson':
            lesson.unit_topic = UnitTopic.objects.get(
                pk=request.POST.get('unit_topic'))
            lesson.save()
            
            return redirect(reverse('uploader:user_lessons'))
    elif 'skip' in request.POST: 
       # we've skipped the linking so redirect back to the correct place
        url = reverse('uploader:index')
        
        if type == 'bookmark':
            url = reverse('uploader:user_bookmarks')
        elif type == 'file':
            url = reverse('uploader:user_files')
        elif type == 'test':
            url = reverse('uploader:user_tests')
        elif type == 'lesson':
            url = reverse('uploader:user_lessons')
            
        return HttpResponseRedirect(url)
    else:
        try:
            form = LinkResourceForm(instance=resource)
        except UnboundLocalError:  # linking a test
            form = LinkResourceForm()

    # FIXME
    if type == 'test':
        subject = test.subject.id
    else:
        subject = None

    return render(request, 'uploader/link_resource.html', {'form': form, 'type': type,
                                                           'subject': subject})

def score_points(user, action):
    """Adds user poinst depending on their action
    """
    points = {
        "Add Resource": 25,
        "Rate": 1
    }
    user_profile = get_user_profile(user)
    user_profile.score += points[action]
    user_profile.save()


@login_required
def profile(request, username=None):

    try:
        if request.user.studentprofile:
            sp = get_object_or_404(StudentProfile, user=request.user)
            form = StudentProfileForm(request.POST or None, instance=sp)

            if request.POST and form.is_valid():
                form.save()
                messages.success(request, "Profile saved successfully")

    except ObjectDoesNotExist:
        if request.user.teacherprofile:
            tp = get_object_or_404(TeacherProfile, user=request.user)
            form = TeacherProfileForm(request.POST or None, instance=tp)

            if request.POST and form.is_valid():
                form.save()
                messages.success(request, "Profile saved successfully")
    finally:
        pass

    return render(request, 'uploader/profile.html', {'form': form})


@login_required
def user_resources(request, user_id=None):
    if not user_id:
        user_id = request.user
    resources = Resource.objects.filter(uploader=user_id).order_by('-pub_date')
    return render(request, 'uploader/user_resources.html',
                  {'resources': resources})


@login_required
def user_files(request, user_id=None):
    if not user_id:
        user_id = request.user
    files = File.objects.filter(uploader=user_id)
    
    #FIXME add into query
    for file in files:
        file.link_count = Resource.objects.filter(file=file).count()
        
    return render(request, 'uploader/user_files.html', {'files': files})


@login_required
def user_bookmarks(request, user_id=None):
    bookmarks = Bookmark.objects.filter(uploader=request.user)

    #FIXME add into query
    for bookmark in bookmarks:
        bookmark.link_count = Resource.objects.filter(
            bookmark=bookmark).count()

    return render(request, 'uploader/user_bookmarks.html',
                  {'bookmarks': bookmarks})


@login_required
def user_questions(request, user_id=None):
    questions = MultipleChoiceQuestion.objects.filter(uploader=request.user)

    return render(request, 'uploader/user_questions.html',
                  {'questions': questions})


@login_required
def user_lessons(request, user_id=None):
    lessons = Lesson.objects.filter(uploader=request.user).order_by('-pub_date')

    return render(request, 'uploader/user_lessons.html', {'lessons': lessons})


@login_required
def edit_lesson(request, code):
    l = get_object_or_404(Lesson, code=code)
    if l.uploader != request.user:
        return HttpResponseForbidden("permission denied")

    form = LessonForm(request.POST or None, instance=l)
    form.fields['groups'].widget = widgets = forms.HiddenInput()

    # FIXME 
    lis = LessonItem.objects.filter(lesson=l)

    # for li in lis:
    #     if hasattr(li, 'type') and li.type == 'resources':
    #         item = Resource.objects.get(slug=li.slug)
    #         li.display = item.get_title()

    if request.POST and form.is_valid():
        lesson = form.save(commit=False)
        # FIXME only need to do this if it's changed
        #lesson.slug = safe_slugify(lesson.title, Lesson)
        url = request.build_absolute_uri(reverse('uploader:lesson',
                                                 args=[lesson.slug]))
        lesson.url = shorten_url(url)
        lesson.save()
        return HttpResponseRedirect(reverse('uploader:user_lessons'))

    context = {'form': form, 'items': lis}

    return render(request, 'uploader/edit_lesson.html', context)


@login_required
def edit_lesson_item(request, id):
    li = get_object_or_404(LessonItem, pk=id)
    if li.lesson.uploader != request.user:
        return HttpResponseForbidden("permission denied")

    form = LessonItemForm(request.POST or None, instance=li)

    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('uploader:user_lessons'))

    return render(request, 'uploader/edit_lesson_item.html', {'form': form})


def lesson(request, slug, code=None):
    # whether or not we are viewing this lesson publically or from a group
    public = False
    
    if not code:
        l = get_object_or_404(Lesson, slug=slug)
        public = True
    else:
        l = get_object_or_404(Lesson, code=code)
        group = Group.objects.filter(code=slug)
        group_lesson = GroupLesson.objects.filter(lesson=l, group=group)
        logger.error(group_lesson.count())
        if group_lesson.count() == 0 and not l.public:
           return HttpResponseForbidden("You do not have access to view this lesson")
        elif group_lesson.count() > 0:
            public = True
        elif l.public:
            public = True

    # if not l.public and l.uploader != request.user:
    #     return HttpResponseForbidden("permission denied")

    if l.objectives:
        l.objectives = render_markdown(l.objectives)

    lis = LessonItem.objects.filter(lesson=l).order_by('order')
    for li in lis:
        if li.content_type and li.object_id:
            type = ContentType.objects.get(app_label="uploader", model=li.content_type)
            li.content = ContentType.get_object_for_this_type(type, pk=li.object_id)
            logger.error(li.content)
            li.type = str(type)
        else:
            li.type = 'task'

    # if this lesson has specified a pre/post be done
    if not public and l.pre_post:
        
        #if we're a student, check if we've already done this
        pre_posts = LessonPrePost.objects.filter(group_lesson=group_lesson)
        
        existing_pre = LessonPrePostResponse.objects.filter(
            pre_post__in=pre_posts,
            student=request.user,
            type='pre')
        if existing_pre.count() > 0:
            existing_pre = True
         
        existing_post = LessonPrePostResponse.objects.filter(
            pre_post__in=pre_posts,
            student=request.user,
            type='post')
        if existing_post.count() > 0:
            existing_post = True   
    
        # get data for graph
        for pre_post in pre_posts:
            pre_responses = LessonPrePostResponse.objects.filter(
                pre_post=pre_post,
                type='pre').aggregate(Avg('score'))
            
            if pre_responses['score__avg']:
                pre_post.pre = pre_responses['score__avg']
            else:
                pre_post.pre = 0
            
            post_responses = LessonPrePostResponse.objects.filter(
                pre_post=pre_post,
                type='post').aggregate(Avg('score'))
            
            if post_responses['score__avg']:
                pre_post.post = post_responses['score__avg']
            else:
                pre_post.post = 0
    else:
        pre_posts = None


    # gather lesson items
    for li in lis:
        li.instructions = render_markdown(li.instructions)
        if li.type == 'resources':
            r = get_object_or_404(Resource, pk=object_id)
            if r.file:
                li.title = r.file.title
            else:
                li.title = r.bookmark.title
        elif li.type == 'notes':
            li.title = get_object_or_404(UnitTopic, pk=object_id).title
        elif li.type == 'test':
            li.title = get_object_or_404(Test, pk=li.object_id)
        elif li.type == 'task':
            pass
        
    context = {'lesson': l, 'lesson_items': lis, 'public': public}
    if pre_posts:
        context['pre_posts'] = pre_posts
        context['existing_post'] = existing_post
        context['existing_pre'] = existing_pre

    return render(request, 'uploader/lesson.html', context)


def lesson_show(request, group_code, code):
    l = get_object_or_404(Lesson, code=code)
    group = get_object_or_404(Group, code=group_code)
    group_lesson = get_object_or_404(GroupLesson, lesson=l, group=group)
    l.url = shorten_lesson_url(request, group.code, l.code)
    
    l.url = string.replace(l.url, "http://", "")
    l.objectives = render_markdown(l.objectives)

    return render(request, 'uploader/lesson_show.html',
                  {'lesson': l})


# def leaderboard(request):
#     context = {}

#     # check if we have enough users yet...
#     user_count = User.objects.count()

#     if user_count >= 10:
#         users = User.objects.filter().order_by('-teacherprofile__score')[:10]
#         for user in users:
#             user.resource_count = Resource.objects.filter(
#                 uploader=user).count()
#         context = {'users': users}

#     # assumes ratings are mostly unique
#     if resource_count >= 10:

#         resources = Resource.objects.filter().order_by('-rating')[:10]

#         for resource in resources:
#             resource.rating = get_resource_rating(resource.id)

#         context['resources'] = resources

#     return render(request, 'uploader/leaderboard.html', context)


def licences(request):
    context = {'licences': Licence.objects.all()}
    return render(request, 'uploader/licences.html', context)


def notes_d(request, slug):
    return notes(request, None, None, None, None, slug)


@login_required
@permission_required(
    'notes.can_edit', '/denied?msg=For editing rights, please email contact@eduresourc.es')
def notes(request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, unit_slug, slug)
    unit_topic = items['unit_topic']
    
    # check if it's locked, if it's not add a lock
    try:
        note = Note.objects.get(unit_topic=unit_topic)
        locked = False
        if note.locked and note.locked_by is not request.user:
            note.locked_until = note.locked_at + datetime.timedelta(minutes=settings.NOTES_LOCK_TIME)
            if note.locked_until >= pytz.utc.localize(datetime.datetime.now()):
                locked = True
        
        if not locked or request.POST.get('renew'):
            note.locked = True
            note.locked_by = request.user
            logger.error(request.user)
            note.locked_at = pytz.utc.localize(datetime.datetime.now())
            note.locked_until = note.locked_at + datetime.timedelta(minutes=settings.NOTES_LOCK_TIME)
            note.save()

        form = NotesForm(request.POST or None, instance=note or None,
             label_suffix='')

        if note.locked_by != request.user:
            form.fields['content'].widget.attrs['disabled'] = 'disabled'

        old_content = note.content
    
    except Note.DoesNotExist:
        note = None

    if request.POST:
        new_note = form.save(commit=False)
        if not note:
            new_note.unit_topic = unit_topic
            new_note.slug = safe_slugify(unit_topic.title, Note)
            new_note.code = generate_code(Note)
            new_note.save()
            NoteHistory(note=new_note,
                        type='full',
                        content=request.POST['content'],
                        user=request.user,
                        comment=None).save()

        if form.is_valid():
            # if it's the same content, no point in adding a diff
            if note and old_content != new_note.content:
                # store the history
                revs = NoteHistory.objects.filter(note=note)
    
                # first go or 20 diffs have passed
                if not Note or revs.count() == 0 or revs.count() % 20 == 0:
                    NoteHistory(note=note,
                                type='full',
                                content=request.POST['content'],
                                user=request.user,
                                comment=None).save()
                else:
                    last_full = NoteHistory.objects.filter(note=note, type='full').order_by('-pub_date')
                    last_full = last_full[0]
                    
                    diff_match_patch.Diff_Timeout = 0
                    diff_obj = diff_match_patch.diff_match_patch()
                    
                    diff = diff_obj.diff_main(last_full.content, request.POST['content'])
                    diff_obj.diff_cleanupEfficiency(diff)
                    patch = diff_obj.patch_toText(diff_obj.patch_make(diff))
                    
                    NoteHistory(note=note,
                                type='diff',
                                content=patch,
                                user=request.user,
                                parent=last_full,
                                comment=None).save()
                            
                new_note.save()
                if not request.POST.get('renew', None):
                    return HttpResponseRedirect(reverse('uploader:view_notes',
                                                        args=[subject_slug, exam_slug, syllabus_slug, unit_slug,
                                                              unit_topic.slug]))
                                                          
    return render(request, "uploader/add_notes.html",
                  {'form': form, 'unit_topic': unit_topic, 'note': note})


@login_required
@permission_required(
    'notes.can_edit', '/denied?msg=For editing rights, please email contact@eduresourc.es')
def notes_history(request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, unit_slug, slug)
    unit_topic = items['unit_topic']
    
    note = Note.objects.get(unit_topic=unit_topic)
    
    history = NoteHistory.objects.filter(note=note).order_by('pub_date')
    
    last_full = None
    for item in history:
        if item.type == 'full':
            last_full = item
        else:
            diff_match_patch.Diff_Timeout = 0
            diff_obj = diff_match_patch.diff_match_patch()
            patch = diff_obj.patch_apply(diff_obj.patch_fromText(item.content), item.parent.content)
            item.content = patch[0]
            diff = diff_obj.diff_main(item.parent.content, item.content)
            diff_obj.diff_cleanupSemantic(diff)
            item.diff = diff_obj.diff_prettyHtml(diff)

    #FIXME reversing the queryset seems to reset it to the original values

    return render(request, 'uploader/notes_history.html', {'history': history})


def view_notes_code(request, code):
    """This is used for linking to notes form the lesson page. It's a bit
    long winded but makes sense as we need this all to resolve the URL
    """
    
    notes = get_object_or_404(Note, code=code)
    unit_topic = notes.unit_topic
    unit = unit_topic.unit
    syllabus = unit.syllabus
    exam_level = syllabus.exam_level
    subject = syllabus.subject
    url = reverse('uploader:view_notes', 
        args=[subject.slug, exam_level.slug, syllabus.slug, unit.slug, 
              unit_topic.slug])
    return redirect(url, permanent=True)


def view_notes(request, subject_slug, exam_slug, syllabus_slug, unit_slug,
               slug):
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, unit_slug, slug)
    unit_topic = items['unit_topic']
    notes_list = Note.objects.filter(unit_topic=unit_topic)
    notes = None
    if notes_list.count() > 0:
        notes = notes_list[0]
        rendered_text = render_markdown(embed_resources(request, notes.content, items['syllabus']))
        notes.content = rendered_text
    context = {'notes': notes, 'unit_topic': unit_topic}
    return render(request, 'uploader/notes.html', context)


@login_required
def upload_image(request):
    form = ImageForm(
        request.POST or None,
        request.FILES or None,
        label_suffix='',
        initial={'uploader': request.user}  # FIXME initial
    )

    if request.method == 'POST' and form.is_valid():
        image = form.save(commit=False)
        image.code = generate_code(Image)
        image.save()
        # FIXME
        return HttpResponseRedirect(
            reverse('uploader:view_image', args=[image.id]))

    return render(request, 'uploader/upload_image.html', {'form': form})


@login_required
def view_image(request, image_id):
    image = get_object_or_404(Image, pk=image_id)
    return render(request, 'uploader/image.html', {'image': image})


@login_required
@user_passes_test(is_teacher, login_url='/denied')
def questions(
        request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, unit_slug, slug)
    unit_topic = items['unit_topic']
    complete_count = 0
    question_count = 0
    questions = None

    if request.POST:
        score = 0

        for question_key in [key for key in request.POST.keys() if
                             key.startswith('question')]:
            question_num = question_key.replace('question', '')
            question = get_object_or_404(MultipleChoiceQuestion,
                                         pk=question_num)
            answer_num = request.POST.get(question_key)
            answer = get_object_or_404(MultipleChoiceAnswer,
                                       question=question, number=answer_num)
            correct = int(answer_num) == int(question.answer)
            answer = MultipleChoiceUserAnswer(
                question=question,
                answer_chosen=answer,
                user=request.user,
                correct=correct
            )
            answer.save()
            if correct:
                score += 1

        t = Test(subject=unit_topic.unit.syllabus.subject,
                 unit_topic=unit_topic).save()
        TestResult(user=request.user, score=score, test=t).save()

        return HttpResponseRedirect(
            reverse('uploader:test_feedback', args=[slug]))
    else:
        # student
        try:
            if request.user.studentprofile:
                # try to find maximum ten questions that the user hasn't taken
                completed_qs = MultipleChoiceUserAnswer.objects.filter(
                    user=request.user,
                    question__unit_topic=unit_topic).values('question_id')
                complete_count = completed_qs.count()

                # FIXME random sorting could be more efficient
                fq = MultipleChoiceQuestion.objects.filter(
                    unit_topic=unit_topic)
                questions = fq.exclude(id__in=completed_qs).order_by('?')[:10]
                question_count = MultipleChoiceQuestion.objects.filter(
                    unit_topic=unit_topic).count()

                # FIXME think there's a function to do this
                for question in questions:
                    answer_list = []
                    answers = MultipleChoiceAnswer.objects.filter(
                        question=question).order_by('number')
                    for answer in answers:
                        answer_list.append(answer)

                    question.answers = answer_list
        except:
            questions = MultipleChoiceQuestion.objects.filter(
                unit_topic=unit_topic)
            # FIXME think there's a function to do this
            for question in questions:
                answer_list = []
                answers = MultipleChoiceAnswer.objects.filter(
                    question=question).order_by('number')
                for answer in answers:
                    answer_list.append(answer)

                question.answers = answer_list

    return render(request, 'uploader/unit_topic_questions.html',
                  {'questions': questions, 'unit_topic': unit_topic,
                   'complete_count': complete_count, 'question_count': question_count})


@login_required
@user_passes_test(is_student, login_url='/denied')
def test(request, code):
    test = get_object_or_404(Test, code=code)
    user_group = StudentGroup.objects.filter(
        student=request.user,
        group=test.group)
    if user_group.count() == 0:
        return HttpResponseRedirect('/denied')
    number_of_questions = test.total
    unit_topic = test.unit_topic
    complete_count = 0
    question_count = 0
    questions = None

    if request.POST:
        score = 0

        for question_key in [key for key in request.POST.keys() if
                             key.startswith('question')]:
            question_num = question_key.replace('question', '')
            question = get_object_or_404(MultipleChoiceQuestion,
                                         pk=question_num)
            answer_num = request.POST.get(question_key)
            answer = get_object_or_404(MultipleChoiceAnswer,
                                       question=question, number=answer_num)
            correct = int(answer_num) == int(question.answer)
            answer = MultipleChoiceUserAnswer(
                test=test,
                question=question,
                answer_chosen=answer,
                user=request.user,
                correct=correct
            )
            answer.save()
            if correct:
                score += 1

        TestResult(user=request.user, score=score, test=test).save()

        return HttpResponseRedirect(
            reverse('uploader:test_feedback', args=[code]))
    else:
        if hasattr(request.user, 'studentprofile'):
                # FIXME random sorting could be more efficient
            questions = MultipleChoiceQuestion.objects.filter(
                unit_topic=unit_topic).order_by('?')[:number_of_questions]

            # FIXME think there's a function to do this
            for question in questions:
                answer_list = []
                answers = MultipleChoiceAnswer.objects.filter(
                    question=question).order_by('number')
                for answer in answers:
                    answer_list.append(answer)

                question.answers = answer_list
        else:
            questions = MultipleChoiceQuestion.objects.filter(
                unit_topic=unit_topic)
            # FIXME think there's a function to do this
            for question in questions:
                answer_list = []
                answers = MultipleChoiceAnswer.objects.filter(
                    question=question).order_by('number')
                for answer in answers:
                    answer_list.append(answer)

                question.answers = answer_list

    return render(request, 'uploader/test.html',
                  {'questions': questions, 'unit_topic': unit_topic,
                   'complete_count': complete_count, 'question_count': question_count})


def test_feedback(request, code):
    test = get_object_or_404(Test, code=code)
    unit_topic = test.unit_topic

    # get all questions for this unit topic
    # FIXME just get answered ones!
    questions = MultipleChoiceQuestion.objects.filter(unit_topic=unit_topic)
    question_list = []

    for question in questions:
        # find user answers
        user_answer = MultipleChoiceUserAnswer.objects.filter(
            question=question, user=request.user)

        # if the user has answered this one
        if user_answer.count() > 0:
            question.answer = MultipleChoiceAnswer.objects.filter(
                question=question)[
                question.answer -
                1]
            question.user_answer = user_answer[0]
            question_list.append(question)

    return render(request, 'uploader/feedback.html',
                  {'questions': question_list, 'unit_topic': unit_topic})


def question(request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    items = hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug, unit_slug, slug)
    unit_topic = items['unit_topic']
    form = MultipleChoiceQuestionForm(request.POST or None)

    if request.POST and form.is_valid():
        number_of_options = request.POST['number_of_options']
        question = MultipleChoiceQuestion(
            number_of_options=number_of_options,
            answer=request.POST['answer'],
            text=request.POST['text'],
            uploader=request.user,
            unit_topic=unit_topic
        )
        question.save()

        for number in range(1, int(number_of_options) + 1):
            text = request.POST['answer' + str(number)]
            answer = MultipleChoiceAnswer(question=question,
                                          text=text,
                                          number=number)
            answer.save()

        if request.POST.get('add_another', False) == 'on':
            url = reverse('uploader:question', args=[slug])
        else:
            url = reverse('uploader:user_questions')

        return HttpResponseRedirect(url)

    return render(request, 'uploader/add_question.html',
                  {'form': form, 'unit_topic': unit_topic})


def student_signup(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/')

    form = StudentForm(request.POST or None)
    if request.POST and form.is_valid():
        g = Group.objects.filter(code=request.POST['group_code'])
        if g.count() == 1:
            s = form.save()
            StudentGroup(group=g[0], student=s).save()
            messages.success(
                request,
                "Thanks for registering. You are now logged in.")
            new_user = authenticate(username=request.POST['username'],
                                    password=request.POST['password'])
            #new_user.groups.add(Group.objects.get(name='student'))
            login(request, new_user)
            return HttpResponseRedirect(reverse('uploader:index'))
        else:
            form.add_error('group_code', "Invalid group code")

    return render(request, 'uploader/student_signup.html', {'form': form})


def teacher_signup(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/')

    form = TeacherForm(request.POST or None)
    if request.POST and form.is_valid():
        form.save()
        messages.success(
            request,
            "Thanks for registering. You are now logged in.")
        new_user = authenticate(username=request.POST['username'],
                                password=request.POST['password'])
        # new_user.groups.add(Group.objects.get(name='teacher'))
        login(request, new_user)
        return HttpResponseRedirect('/')

    return render(request, 'uploader/teacher_signup.html', {'form': form})


@login_required
def groups_list(request):
    groups = Group.objects.filter(teacher=request.user)
    return render(request, 'uploader/groups.html', {'groups': groups})


@login_required
def groups(request, slug=None):
    group = None

    if slug:
        group = get_object_or_404(Group, slug=slug)
        if group.teacher != request.user.teacherprofile and not (
                request.user.is_superuser()):
            return HttpResponseForbidden("No stairway, denied!")
    else:
        group = Group(teacher=request.user)


    if request.POST:
        form = GroupForm(request.POST, instance=group)

        if form.is_valid():
            g = form.save(commit=False)
            g.slug = safe_slugify(g.name, Group)
            g.code = generate_code(Group)
            g.save()
            return HttpResponseRedirect(reverse('uploader:groups_list'))
    else:
        form = GroupForm(instance=group)

    return render(request, 'uploader/add_group.html', {'form': form})


@login_required
def group(request, code):
    group = get_object_or_404(Group, code=code)

    if request.POST:
        lesson = Lesson.objects.get(pk=request.POST['lesson'])
        GroupLesson(group=group, lesson=lesson, set_by=request.user).save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        form = GroupLessonForm()
        form.fields['lesson'].queryset = Lesson.objects.filter(uploader=request.user).order_by('-pub_date')[:10]
        student_group = StudentGroup.objects.filter(group=group)
        tests = Test.objects.filter(teacher=request.user).order_by('-pub_date')
        lessons = GroupLesson.objects.filter(group=group).order_by('-date', '-pub_date')

        for lesson in lessons:
            lesson.link = shorten_lesson_url(request, group.code, lesson.lesson.code)
            lesson.feedback = LessonPrePostResponse.objects.filter(type='post', pre_post__group_lesson=lesson).aggregate(Avg('score'))['score__avg']

        for student_group_object in student_group:
            student = student_group_object.student
            student.results = []
            tests_taken = 0
            for test in tests:
                test_result = TestResult.objects.filter(
                    user=student,
                    test=test).order_by('-score')
    
                tests_taken += test_result.count()
                if test_result.count() > 0:
                    student.results.append(
                        {'score': test_result[0].score, 'total': test.total})
                else:
                    student.results.append({'total': test.total})
        # return HttpResponse(tests_taken)
        context = {'group': group, 'students': student_group, 'tests': tests,
                   'lessons': lessons, 'form': form}

    return render(request, 'uploader/group.html', context)


@login_required
def add_test(request):
    form = TestForm(request.POST or None)
    form.fields['group'].queryset = Group.objects.filter(teacher=request.user)

    if request.POST:
        if form.is_valid():
            subject = get_object_or_404(Subject, pk=request.POST['subject'])
            group = get_object_or_404(Group, pk=request.POST['group'])
            code = generate_code(Test)

            Test(subject=subject,
                 teacher=request.user,
                 group=group,
                 code=code,
                 total=request.POST['total']
                 ).save()

            return redirect(reverse('uploader:link_test', args=[code]))
    return render(request, 'uploader/add_test.html', {'form': form})


@login_required
def link_test(request, code):
    test = get_object_or_404(Test, code=code)
    return link_resource(request, 'test', test)
    

@login_required    
def lesson_present(request, group_code, code):
    lesson = get_object_or_404(Lesson, code=code)
    group = get_object_or_404(Group, code=group_code)
    group_lesson = get_object_or_404(GroupLesson, group=group, lesson=lesson)
    lis = LessonItem.objects.filter(lesson=lesson)
    context = {'lesson': lesson, 'lis': lis}
    return render(request, 'uploader/lesson_present.html', context)


def denied(request):
    if hasattr(request.GET, 'msg'):
        msg = request.GET['msg']
    else:
        msg = ""
    return render(request, 'uploader/permission_denied.html', {'msg': msg})
    

@login_required    
def delete_lesson(request, code):
    lesson = get_object_or_404(Lesson, code=code)
    if lesson.uploader == request.user:
        messages.success(request,"Lesson %s deleted", lesson.title)
        lesson.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER',
                                                             '/'))
    else:
        return render(request, 'uploader/permission_denied.html')


@login_required
def assignment(request, code=None):
    if code:
        assignment = get_object_or_404(Assignment, code=code)
    else:
        assignment = None

    form = AssignmentForm(request.POST or None, instance=assignment)
    form.fields['group'].queryset = Group.objects.filter(teacher=request.user)
    if request.POST and form.is_valid():
        if code:
            form.save()
        else:
            rp = request.POST
            group = get_object_or_404(Group, pk=rp.get('group'))
            Assignment(title=rp.get('title'),
                       code=generate_code(Assignment),
                       group=group,
                       teacher=request.user,
                       description=rp.get('description'),
                       deadline=rp.get('deadline')).save()

        return HttpResponseRedirect(reverse('uploader:index'))
        
    return render(request, 'uploader/assignment.html', {'form': form})
    

@login_required
def delete_assignment(request, code):
    assignment = get_object_or_404(Assignment, code=code)
    
    if assignment.teacher == request.user:
        assignment.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('uploader:index')))
    else:
        return render(request, 'uploader/permission_denied.html', {})


@login_required    
def view_assignment(request, code):
    """Shows an assignment view, for teacher this is a list of submissions,
    for students it allows them to submit an assignment and see previous 
    submissions
    """
    assignment = get_object_or_404(Assignment, code=code)

    context = {'assignment': assignment}
    
    template = 'uploader/student_assignment.html'
    
    if user_type(request.user) == 'teacher':
        students = StudentGroup.objects.filter(group=assignment.group)
        student_ids = students.values('student_id')
        
        submissions = AssignmentSubmission.objects.filter(student_id__in=student_ids,
                                                              assignment=assignment)
    
        #FIXME can we do this in one query?
        submission_count = 0
        late_count = 0
        absent_count = 0
        for student in students:
            student = student.student
            try:
                student.submission = submissions.get(student=student)
                student.submission.diff = assignment.deadline - student.submission.submitted
                student.submission.late = False
                
                # # FIXME only currently one, might be multiple 
                # student.feedback = Feedback.objects.get(assignment_submission=student.submission)
    
                if student.submission.get_status_display() == 'Absent': 
                    absent_count += 1
                else:
                    submission_count += 1
    
                if student.submission.diff < datetime.timedelta(minutes=0):
                    student.submission.late = True
                    late_count += 1
                    submission_count += 1

    
            except AssignmentSubmission.DoesNotExist:
                pass

        # get values for submission status bar
        assignment.total = students.count()
        
        try:
            assignment.submissions = submission_count
            assignment.late = late_count
            assignment.absent = absent_count
            assignment.on_time = submission_count - assignment.late
            assignment.not_submitted = assignment.total - assignment.on_time - assignment.late - assignment.absent
            
            assignment.submissions_percentage = int(submission_count / assignment.total * 100)
            assignment.late_percentage = int(late_count / assignment.total * 100)
            assignment.absent_percentage = int(absent_count / assignment.total * 100)
            assignment.on_time_percentage = int((assignment.submissions - assignment.late) / assignment.total * 100)
            assignment.not_submitted_percentage = int(assignment.not_submitted / assignment.total * 100)
        
        except ZeroDivisionError:
            assignment.submissions_percentage = 0
            assignment.late_percentage = 0
            assignment.absent_percentage = 0
            assignment.not_submitted_percentage = 100
            

        template = 'uploader/teacher_assignment.html'
        context['students'] = students
    else: # student
        if request.POST:
            a_s = AssignmentSubmission(student=request.user, assignment=assignment)
            a_s.save()
            Feedback(assignment_submission=a_s).save()
            AssignmentSubmissionFile(assignment_submission=a_s,
                                     file=request.FILES.get('file'),
                                     comments=request.POST.get('comments')).save()
                                     
            return HttpResponseRedirect(reverse('uploader:index'))
        else:
            template = 'uploader/student_assignment.html'
            form = AssignmentSubmissionFileForm(request.POST or None)
            previous_submissions = AssignmentSubmission.objects.filter(
                student=request.user, assignment=assignment)
            context['form'] = form
            context['previous_submissions'] = previous_submissions


    
    return render(request, template, context)
    

def mark_assignment(request, assignment_code, submission_id=None, absent=None, student_id=None):
    assignment = get_object_or_404(Assignment, code=assignment_code)
    submission = get_object_or_404(AssignmentSubmission, pk=submission_id)

    if absent == 'absent':
        student = get_object_or_404(User, pk=student_id)
        sub = AssignmentSubmission(student=student, assignment=assignment)
        sub.status == 5
        sub.save()

        return HttpResponseRedirect(reverse('uploader:view_assignment', args=[assignment.code]))

    else:
        form = MarkAssignmentForm(request.POST or None, instance=submission)

        if request.POST and form.is_valid():
            new_assignment = form.save(commit=False)
            if assignment.grading.type == 1: #numerical
                pass
            elif assignment.grading.type == 2: #options
                new_assignment.result = request.POST.get('grade_options') or None
                
            new_assignment.save()
        
            return HttpResponseRedirect(reverse('uploader:view_assignment', args=[submission.assignment.code]))
            
        else:
            files = AssignmentSubmissionFile.objects.filter(assignment_submission=submission)
            form.fields['result'].widget.attrs.update({
                'placeholder': 'out of ' + str(submission.assignment.total)
            })
            
            if assignment.grading.type == 1: #numerical
                pass
            elif assignment.grading.type == 2: #options
                fields =[('', '---------')]
                # fields = []
                grade_fields = GradeOptions.objects.filter(grading=assignment.grading).order_by('order')
                for field in grade_fields:
                    fields.append((field.value, field.grade))
                form.fields['grade_options'].choices = fields
                form.fields['grade_options'].queryset = fields

                if submission:
                    form.fields["grade_options"].initial = submission.result
                form.fields['result'].widget = forms.HiddenInput()
    
        context = {'submission': submission, 'files': files, 'form': form}
        
        return render(request, 'uploader/mark_assignment.html', context)


def user_grading(request):
    public_grading = Grading.objects.filter(public=True)
    for grading in public_grading:
        if grading.type == 2:
            grading.options = GradeOptions.objects.filter(grading=grading)
        elif grading.type == 1:
            grading.options = NumericalGrade.objects.filter(grading=grading)
        
    user_grading = Grading.objects.filter(user=request.user).order_by('type').exclude(pk__in=public_grading)
    # FIXME
    for grading in user_grading:
        if grading.type == 2:
            grading.options = GradeOptions.objects.filter(grading=grading)
        elif grading.type == 1:
            grading.options = NumericalGrade.objects.filter(grading=grading)
    
    context = {'public_grading': public_grading, 'user_grading': user_grading}
    
    return render(request, 'uploader/grading.html', context)


@user_passes_test(is_teacher, login_url='/denied')
def grading(request, id=None):
    form = GradingForm(request.POST or None)
    if request.POST:
        form_data = request.POST
        title = form_data.get('title')
        grades = form_data.getlist('grade[]')
        
        if form_data.get('numerical'):
            
            boundaries = form_data.getlist('boundary[]')

            grading = Grading(
                title=form_data.get('title'),
                user=request.user,
                type=1)
            grading.save()
            
            for grade, boundary in zip(grades, boundaries):
                if grade and boundary:
                    ng = NumericalGrade(
                        grading=grading, 
                        grade=grade, 
                        upper_bound=boundary)
                    ng.save()

        elif form_data.get('options'):
            grading = Grading(
                title=form_data.get('title'),
                user=request.user,
                type=2)
            grading.save()
            
            grades = form_data.getlist('option_grade[]')
            descriptions = form_data.getlist('description[]')

            i = 1
            for grade, description in zip(grades, descriptions):
                if grade:
                    ng = GradeOptions(
                        grading=grading,
                        value=i,
                        grade_long=description,
                        grade=grade, 
                        order=i)
                    ng.save()
                    i += 1


            return HttpResponseRedirect(reverse('uploader:user_grading'))
    return render(request, 'uploader/add_grading.html', {'form': form})


@login_required
def user_tests(request):
    tests = Test.objects.filter(teacher=request.user)

    return render(request, 'uploader/user_tests.html', {'tests': tests})


@user_passes_test(is_teacher, login_url='/denied')
def lesson_creator(request):
    user_resources = Resource.objects.filter(uploader=request.user)[:30]
    user_tests = Test.objects.filter(teacher=request.user)[:30]
    form = LessonForm(request.POST or None)
    
    if request.POST and form.is_valid():
        form_data = request.POST
        
        # do a quick check for odd lesson items so we're not left with a 
        # dangling lesson
        items_okay = True
        instructions = form_data.getlist('instructions[]')
        types = form_data.getlist('types[]')
        ids = form_data.getlist('ids[]')
        for i in range(len(ids)):
            if 'task' in types[i] and len(instructions[i]) == 0:
                items_okay = False
            
        if items_okay:
            public = True if form_data.get('public') else False
            slug = safe_slugify(form_data.get('title'), Lesson)
    
            show_to_students = False
            if form_data.get('show_presentation_to_students') == 'on':
                show_to_students = True
                
            # only only pre_posts if we've got a group to assign them to
            groups = form_data.getlist('groups')
            if len(groups) > 0:
                pre_posts = form_data.getlist('pre_post_vals[]', None)
                pre_post = True if pre_posts else None
            else:
                pre_post = False
    
            # create the lesson
            l = Lesson(title=form_data.get('title'),
                       slug=slug,
                       objectives=form_data.get('objectives', None),
                       uploader=request.user,
                       presentation=request.FILES.get('presentation', None),
                       show_presentation_to_students=show_to_students,
                       public=public,
                       pre_post=pre_post or False,
                       code=generate_code(Lesson)
                       )
            l.save()
    
            # create the items that compose the lessons
            instructions = form_data.getlist('instructions[]')
            types = form_data.getlist('types[]')
            ids = form_data.getlist('ids[]')
            for i in range(len(ids)):
                # FIXME why is there a space anyway?
                types[i] = str(types[i].strip())
                if types[i] == 'task':
                    types[i] = None
                    ids[i] = None
                elif types[i] == 'resource':
                    types[i] = ContentType.objects.get_for_model(Resource)
                elif types[i] == 'notes':
                    types[i] = ContentType.objects.get_for_model(Note)
                elif types[i] == 'test':
                    types[i] = ContentType.objects.get_for_model(Test)
                    
                LessonItem(lesson=l,
                           content_type=types[i],
                           object_id=ids[i],
                           order=(i+1),
                           instructions=instructions[i]).save()
            
             
            # assign lessons to those groups and deal with pre/posts
            if len(groups) > 0:
                for group_id in groups:
                    group = get_object_or_404(Group, pk=group_id)
                    gl = GroupLesson(group=group, lesson=l, set_by=request.user)
                    gl.save()
            
                    if pre_posts:
                        for pre_post in pre_posts:
                            LessonPrePost(text=pre_post, group_lesson=gl).save()
                            
            return redirect(reverse('uploader:lesson', args=[l.slug]))   
            
        else:
            form.add_error(None, "Please add a instruction to all tasks")

    context = {'form': form, 'user_resources': user_resources,
               'user_tests': user_tests}
    return render(request, 'uploader/lesson_creator.html', context)
    

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ajax views

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


def get_syllabuses(request, subject_id):
    subject = Subject.objects.get(pk=subject_id)
    syllabuses = Syllabus.objects.filter(subject=subject)
    syllabuses_dict = {}
    for syllabus in syllabuses:
        syllabuses_dict[syllabus.id] = str(syllabus)
    return JsonResponse(syllabuses_dict)


def get_units(request, syllabus_id):
    syllabus = Syllabus.objects.get(pk=syllabus_id)
    units = Unit.objects.filter(syllabus=syllabus)
    units_dict = {}
    for unit in units:
        units_dict[unit.id] = str(unit)
    return JsonResponse(units_dict)


def get_unit_topics(request, unit_id):
    unit = Unit.objects.get(pk=unit_id)
    unit_topics = UnitTopic.objects.filter(
        unit=unit).order_by(
        'section',
        'pub_date')
    unit_topics_dict = list()
    for unit_topic in unit_topics:
        if unit_topic.section:
            section = unit_topic.section
        else:
            section = ""
        unit_topics_dict.append(
            {'id': unit_topic.id, 'unit_topic': str(unit_topic), 'section': section})
    return JsonResponse(unit_topics_dict, safe=False)

def vote(request, content_type, object_id, vote):
    """just silently ignore non-logged in ratings
    """
    if not request.user.is_authenticated():
        return HttpResponse("Please login to vote")
    else:
        model = apps.get_model(app_label='uploader', model_name=content_type)
        vote = Vote(
            user=request.user,
            content_type=ContentType.objects.get_for_model(model),
            object_id=object_id,
            vote=vote
        )
    try:
        vote.save()
        score_points(request.user, "Rate")
        return HttpResponse("Thank you for voting")
    except IntegrityError as e:
        return HttpResponse("You have already voted")
        pass

    


def get_url_description(request, url):
    json = {}
    url_info = extract(url)
    try:
        json['description'] = url_info['description'] or ""
        json['title'] = url_info['title'] or ""
    except KeyError:
        pass

    return JsonResponse(json)


def bulk_bookmark_update(request, action, ids):
    """ Allows a user to bulk-update bookmarks
    """
    try:
        id_list = ids.split(',')
        if action in [
                'general', 'news', 'blog', 'video', 'image', 'info', 'delete']:
            if action == 'delete':
                Bookmark.objects.filter(
                    id__in=id_list,
                    uploader=request.user).delete()
            else:
                Bookmark.objects.filter(
                    id__in=id_list,
                    uploader=request.user).update(
                    type=action)
    except Exception as e:
        logger.error(e)

    return HttpResponse()

def pre_post(request, action, id):
    lesson = get_object_or_404(Lesson, pk=id)
    pre_posts = LessonPrePost.objects.filter(lesson=lesson)
    if action == 'pre':
        for i in range(0, pre_posts.count()):
            pre = request.POST.get('pre[' + str(i + 1) + ']')
            if pre:
                try:
                    LessonPrePostResponse(pre_post=pre_posts[i],
                                          student=request.user,
                                          type='pre',
                                          score=pre).save()
                except IntegrityError as e:
                    pass
    elif action == 'post':
        for i in range(0, pre_posts.count()):
            pre = request.POST.get('post[' + str(i + 1) + ']')
            if pre:
                try:
                    LessonPrePostResponse(pre_post=pre_posts[i],
                                          student=request.user,
                                          type='post',
                                          score=pre).save()
                except IntegrityError as e:
                    pass

    return HttpResponse("")
    

def get_object_from_code(request, code, type):
    if type == 'notes':
        note = Note.objects.get(code=code)
        response = {'id': note.id, 'title': note.unit_topic.title}
    elif type == 'resource':
        resource = Resource.objects.get(code=code)
        # FIXME jesusfuck
        response = {'id': resource.id, 'title': resource.file.title if resource.file else resource.bookmark.title}
    elif type == 'test':
        test = Test.objects.get(code=code)
        response = {'id': test.id, 'title': test.unit_topic.title}

    return JsonResponse(response)
