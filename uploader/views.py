import re
import requests
import logging
import json
import time
import urllib2
import mimetypes

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

        # get messages TODO use constants
        user_messages = Message.objects.filter(user_to=request.user.id)
        announce_messages = Message.objects.filter(type=2)
        sticky_messages = Message.objects.filter(type=3)

        context = {
            'subjects': subjects,
            'user_messages': user_messages | announce_messages | sticky_messages,
            'homepage': True
        }
        return render(request, 'uploader/index.html', context)
    else:
        if hasattr(request.user, 'teacherprofile'):
            groups = Group.objects.filter(teacher=request.user)
            tests = Test.objects.filter(group__in=groups)[:5]

            context = {'groups': groups, 'tests': tests}
            return render(request, 'uploader/teacher_home.html', context)
        else:
            # FIXME use a filter
            groups = StudentGroup.objects.filter(student=request.user)
            test_list = {}
            for group in groups:
                tests = Test.objects.filter(group=group.group)
                if tests.count() > 0:
                    test_list[group.group.name] = tests
                    for test in tests:
                        try:
                            result = TestResult.objects.get(
                                test=test,
                                user=request.user)
                            test.result = result
                        except TestResult.DoesNotExist:
                            pass

            return render(
                request, 'uploader/student_home.html', {'tests': test_list})


def subjects(request):
    subjects = Subject.objects.filter(active=1)

    context = {
        'subjects': subjects,
    }
    return render(request, 'uploader/subjects.html', context)


@login_required
def favourites(request):
    context = {}
    if request.user.is_authenticated():
        try:
            subjects = request.user.teacherprofile.subjects.all()
        except ObjectDoesNotExist:
            subjects = request.user.studentprofile.subjects.all()

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
    syllabus = get_object_or_404(Syllabus, slug=slug)
    resources = Resource.objects.filter(
        syllabus__id=syllabus.id,
        unit__isnull=True,
        unit_topic__isnull=True)

    context = {'syllabus': syllabus, 'resources': resources}
    return render(request, 'uploader/syllabus_resources.html', context)


def unit_topic(
        request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    unit_topic.description = render_markdown(unit_topic.description)
    resources = Resource.objects.filter(unit_topic=unit_topic).count()
    notes = Note.objects.filter(unit_topic=unit_topic).count()
    question = MultipleChoiceQuestion.objects.filter(unit_topic=unit_topic)
    questions = question.count()
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
               'related_topics': related, 'favourite': favourite}
    return render(request, 'uploader/unit_topic.html', context)


def unit_topic_resources(
        request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    # resources = Resource.objects.filter(unit_topic=unit_topic).values()

    # FIXME when Django 1.8 gets COALESCE we get set a default
    # (https://code.djangoproject.com/ticket/10929)

    # resources = Resource.objects.filter(unit_topic=unit_topic).annotate(avg_rating=Coalesce(Avg('rating__rating'), 3.0)).order_by('-avg_rating')
    resources = Resource.objects.filter(
        unit_topic=unit_topic).annotate(
        avg_rating=Avg('rating__rating')).order_by('-avg_rating')

    context = {'unit_topic': unit_topic, 'resources': resources}
    return render(request, 'uploader/unit_topic_resources.html', context)


def unit_resources(request, subject_slug, exam_slug, syllabus_slug, unit_slug):
    unit = get_object_or_404(Unit, slug=unit_slug)
    resources = Resource.objects.filter(
        unit__id=unit.id,
        unit_topic__isnull=True)

    context = {'unit': unit, 'resources': resources}
    return render(request, 'uploader/unit_resources.html', context)


def syllabuses(request, subject_slug, exam_slug):
    """View list of syllabuses for a subject and level,
    e.g. {AQA, OCR} GCSE Maths
    """
    subject = get_object_or_404(Subject, slug=subject_slug)
    level = get_object_or_404(ExamLevel, slug=exam_slug)

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
    syllabus = get_object_or_404(Syllabus, slug=slug)
    syllabus.description = render_markdown(syllabus.description)
    units = Unit.objects.filter(syllabus__id=syllabus.id).order_by('order',
                                                                   'title')

    favourite = False
    if request.user.is_authenticated():
        try:
            favourite = SyllabusFavourite.objects.get(
                syllabus=syllabus,
                user=request.user)
        except ObjectDoesNotExist:
            pass

    context = {'syllabus': syllabus, 'units': units, 'favourite': favourite}
    return render(request, 'uploader/syllabus.html', context)


def unit(request, subject_slug, exam_slug, syllabus_slug, slug):
    """A single unit view
    """
    unit = get_object_or_404(Unit, slug=slug)
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

    resources = None

    if unit_topics.count() == 0:
        resources = Resource.objects.filter(unit__id=unit.id)

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

    context = {
        'resource': resource,
        'rating': get_resource_rating(resource.id),
        'rating_val': get_resource_rating(resource.id, 'values')
    }
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

    return render_to_response(template,
                              context_instance=RequestContext(request, context))


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


def bookmark(request, slug=None):
    bookmark = None

    # stick the referer in so if we're coming from deep in user bookmarks
    # we get back to the same place
    if 'edit' not in request.META.get('HTTP_REFERER', ""):
        request.session['refer'] = request.META.get('HTTP_REFERER', None)

    if slug:
        bookmark = get_object_or_404(Bookmark, slug=slug)
        if bookmark.uploader != request.user and not request.user.is_superuser():
            return HttpResponseForbidden("No stairway, denied!")
    else:
        if request.user.is_authenticated():
            bookmark = Bookmark(uploader=request.user)
        else:
            bookmark = Bookmark()

    if request.POST:
        form = BookmarkForm(request.POST, instance=bookmark)

        if form.is_valid():
            if not slug:
                # insert
                bookmark = form.save(commit=False)
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
                return HttpResponseRedirect(
                    request.session['refer'] or reverse('uploader:user_bookmarks'))

    else:
        form = BookmarkForm(instance=bookmark)

    return render_to_response('uploader/add_bookmark.html', {
        'form': form,
    }, context_instance=RequestContext(request))


def link_file(request, slug):
    file = get_object_or_404(File, slug=slug)
    return link_resource(request, 'file', slug)


def link_bookmark(request, slug):
    bookmark = get_object_or_404(Bookmark, slug=slug)
    return link_resource(request, 'bookmark', slug)


def link_resource(request, type, slug):
    bookmark = None
    file = None
    test = None

    if type == 'bookmark':
        bookmark = get_object_or_404(Bookmark, slug=slug)
    elif type == 'file':
        file = get_object_or_404(File, slug=slug)
    elif type == 'test':
        test = get_object_or_404(Test, code=slug)

    if type == 'bookmark' or type == 'file':
        if request.user.is_authenticated():
            resource = Resource(uploader=request.user, file=file or None,
                                bookmark=bookmark or None, approved=False)
        else:
            resource = Resource(file=file or None,
                                bookmark=bookmark or None, approved=False)

    if request.method == 'POST':
        if type == 'bookmark' or type == 'file':
            form = LinkResourceForm(request.POST, instance=resource)
            if form.is_valid():
                resource = form.save(commit=False)
                # work out slug
                if resource.file is not None:
                    resource.slug = resource.file.slug
                else:
                    resource.slug = resource.bookmark.slug

                # check if we already have one with that name, append number if
                # so
                starts_with = resource.slug + '-'
                starting_matches = Resource.objects.filter(
                    slug__startswith=starts_with).count()
                exact = Resource.objects.filter(
                    slug=resource.slug).count()

                num_results = exact + starting_matches

                if num_results > 0:
                    append = num_results + 1
                    resource.slug += '-' + str(append)

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
            # FIXME my tests
            return redirect("/")
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
    points = {
        "Add Resource": 25,
        "Rate": 1
    }
    user_profile = None
    if user.teacherprofile:
        user_profile = TeacherProfile.objects.get(user=user.id)
    elif user.studentprofile:
        user_profile = StudentProfile.objects.get(user=user.id)

    if user_profile:
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
    resources = Resource.objects.filter(uploader=user_id).annotate(
        avg_rating=Avg('rating__rating')).order_by('-avg_rating')

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


def check_lesson_items(request, num_items):
    """check that the lesson items aren't missing any values
    """
    rp = request.POST
    for i in range(1, num_items + 1):
        _i = str(i)
        if not rp.get('order' + _i, None):
            return False
    return True


# FIXME this is too hacky
@login_required
def user_lessons(request, user_id=None):
    form = LessonForm(request.POST or None, request.FILES or None)
    
    form_errors = []
    form_data = None

    if request.POST:
        
        form_data = request.POST
        
        if form_data.get('submit', False) == 'delete':
            request.session['resources'] = None
            request.session['notes'] = None
            request.session['tests'] = None
            request.session['tasks'] = None

        elif form_data.get('add_task'):
            add_item_to_lesson(request, int(time.time()), 'task')
        elif not form_data.get('title'):
            form_errors.append('Please enter a lesson title')
        else:
            num_items = 0
            rs = request.session
            for types in ('resources', 'notes', 'tests', 'tasks'):
                if types in rs and rs[types]:
                    num_items += len(rs[types])

            # this checks we've not missed an order number out
            items_okay = check_lesson_items(request, num_items)

            if num_items > 0 and items_okay:
                public = True if form_data.get('public') else False
                slug = safe_slugify(form_data.get('title'), Lesson)

                show_to_students = False
                if form_data.get('show_presentation_to_students') == 'on':
                    show_to_students = True
                    
                pre_posts = form_data.getlist('pre_post_vals[]', None)
                pre_post = True if pre_posts else None

                l = Lesson(title=form_data.get('title'),
                           slug=slug,
                           objectives=form_data.get('objectives', None),
                           uploader=request.user,
                           presentation=form_data.get('presentation', None),
                           show_presentation_to_students=show_to_students,
                           public=public,
                           pre_post=pre_post or False,
                           code=random_key(3, 'Lesson')
                        #   date_for=form_data.get('date_for') or None,
                        #   lesson=form_data.get('lesson') or None
                           )
                url = request.build_absolute_uri(reverse('uploader:lesson',
                                                         args=[slug]))

                l.url = shorten_url(url)
                l.save()
                
                if form_data.get('group', None):
                    group = Group.objects.filter(pk=form_data.get('group'))
                    if group.count() > 0:
                        group = group[0]
                        GroupLesson(group=group, lesson=l, set_by=request.user).save()

                if check_lesson_items(request, num_items):
                    for i in range(1, num_items + 1):
                        _i = str(i)
                        # don't save blank tasks
                        if (len(form_data.get('instructions' + _i)) == 0 and
                                form_data.get('type' + _i) == 'task'):
                            pass
                        else:
                            type = form_data.get('type' + _i, None)
                            if type == 'resources':
                                resource = Resource.objects.get(slug=form_data.get('slug' + _i, None))
                                id = resource.id
                                content_type = ContentType.objects.get_for_model(resource)
                            elif type == 'notes':
                                note = Note.objects.get(slug=form_data.get('slug' + _i, None))
                                id = note.id
                                content_type = ContentType.objects.get_for_model(note)
                            elif type == 'test':
                                test = Test.objects.get(slug=form_data.get('slug' + _i, None))
                                id = test.id
                                content_type = ContentType.objects.get_for_model(test)
                            elif type == 'tasks':
                                content_type = None
                                id = None


                            li = LessonItem(
                                lesson=l,
                                content_type=content_type,
                                object_id=id,
                                order=form_data.get('order' + _i, None),
                                instructions=form_data.get('instructions' + _i, None),
                            )

                            li.save()
                            
                if pre_posts:
                    for pre_post in pre_posts:
                        LessonPrePost(text=pre_post, lesson=l).save()
                
                request.session['resources'] = None
                request.session['notes'] = None
                request.session['tests'] = None
                request.session['tasks'] = None
                return HttpResponseRedirect(request.META.get('HTTP_REFERER',
                                                             '/'))
            elif not items_okay:
                form_errors.append('Please add an order to all items')

    # check if we've got any stuff added to lesson
    resources = request.session.get('resources', None)
    resource_list = []
    count = 1

    if resources:
        for resource in resources:
            _resource = get_object_or_404(Resource, slug=resource)
            if _resource is not None:
                _resource.count = count
                resource_list.append(_resource)
                count += 1

    notes = request.session.get('notes', None)
    notes_list = []
    if notes:
        for note in notes:
            unit_topic = get_object_or_404(UnitTopic, slug=note)
            _note = get_object_or_404(Note, unit_topic=unit_topic)
            if _note is not None:
                _note.count = count
                notes_list.append(_note)
                count += 1

    tests = request.session.get('tests', None)
    tests_list = []
    if tests:
        for test in tests:
            _test = get_object_or_404(UnitTopic, slug=test)
            if _test is not None:
                _test.count = count
                tests_list.append(_test)
                count += 1

    tasks = request.session.get('tasks', None)
    tasks_list = []
    if tasks:
        for task in tasks:
            task = count
            tasks_list.append(task)
            count += 1

    lessons = Lesson.objects.filter(
        uploader=request.user).order_by('-pub_date')
    paginator = Paginator(lessons, 15)

    page = request.GET.get('page')
    try:
        lessons = paginator.page(page)
    except PageNotAnInteger:
        lessons = paginator.page(1)
    except EmptyPage:
        lessons = paginator.page(paginator.num_pages)

    now = int(time.time())

    return render(request, 'uploader/user_lessons.html',
                  {'resources': resource_list, 'notes': notes_list,
                   'tests': tests_list, 'lessons': lessons, 'tasks': tasks_list,
                   'time': now, 'form_errors': form_errors, 
                   'form_data': form_data, 'form': form})


@login_required
def edit_lesson(request, slug):
    l = get_object_or_404(Lesson, slug=slug)
    if l.uploader != request.user:
        return HttpResponseForbidden("permission denied")

    form = LessonForm(request.POST or None, instance=l, user=request.user)
    form.group.queryset = Group.objects.filter(teacher=request.user)

    lis = LessonItem.objects.filter(lesson=l)

    for li in lis:
        if li.type == 'resources':
            item = Resource.objects.get(slug=li.slug)
            li.display = item.get_title()

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
            pass # viewing group lesson
        elif l.public:
            public = True

    # if not l.public and l.uploader != request.user:
    #     return HttpResponseForbidden("permission denied")

    if l.objectives:
        l.objectives = render_markdown(l.objectives)

    lis = LessonItem.objects.filter(lesson=l).order_by('order')
    for li in lis:
        type = ContentType.objects.get(app_label="uploader", model=li.content_type)
        li.content = ContentType.get_object_for_this_type(type, pk=li.object_id)
        logger.error(li.content)
        li.type = str(type)

    # if this lesson has specified a pre/post be done
    if l.pre_post:
        
        #if we're a student, check if we've already done this
        pre_posts = LessonPrePost.objects.filter(lesson=l)
        
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


def lesson_show(request, slug):
    l = get_object_or_404(Lesson, slug=slug)
    l.url = string.replace(l.url, "http://", "")
    l.objectives = render_markdown(l.objectives)

    return render(request, 'uploader/lesson_show.html',
                  {'lesson': l})


@login_required
def add_item_to_lesson(request, slug, type):

    if type == 'resource':
        resource = get_object_or_404(Resource, slug=slug)
        if resource:
            if ('resources' not in request.session or
                    request.session['resources'] is None):
                request.session['resources'] = (slug,)
            elif slug not in request.session['resources']:
                request.session['resources'].append(slug)
            request.session.modified = True
            messages.success(request, "Added to a new lesson, go to My " +
                                      "Folder > Lessons to view")

    elif type == 'notes':
        unit_topic = get_object_or_404(UnitTopic, slug=slug)
        notes = get_object_or_404(Note, unit_topic=unit_topic)
        if notes:
            logger.error("saving: " + slug)
            logger.error("saving: " + str(notes.slug))
            logger.error("saving: " + str(unit_topic))
            if ('notes' not in request.session or
                    request.session['notes'] is None):
                request.session['notes'] = (slug,)
            elif slug not in request.session['notes']:
                request.session['notes'].append(slug)
            request.session.modified = True
            messages.success(request, "Added to a new lesson, go to My " +
                                      "Folder > Lessons to view")

    elif type == 'test':
        unit_topic = get_object_or_404(UnitTopic, slug=slug)
        if request.session.get('tests', None) is None:
            request.session['tests'] = (slug,)
        elif slug not in request.session['tests']:
            request.session['tests'].append(slug)
        request.session.modified = True
        messages.success(request, "Added to a new lesson, go to My " +
                                  "Folder > Lessons to view")

    elif type == 'task':
        if request.session.get('tasks', None) is None:
            request.session['tasks'] = (slug,)
        elif slug not in request.session['tasks']:
            request.session['tasks'].append(slug)
        request.session.modified = True

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def leaderboard(request):
    context = {}

    # check if we have enough users yet...
    user_count = User.objects.count()

    if user_count >= 10:
        users = User.objects.filter().order_by('-teacherprofile__score')[:10]
        for user in users:
            user.resource_count = Resource.objects.filter(
                uploader=user).count()
            user.rating_count = Rating.objects.filter(user=user).count()
        context = {'users': users}

    resource_count = Rating.objects.count()
    # assumes ratings are mostly unique
    if resource_count >= 10:

        resources = Resource.objects.filter().order_by('-rating')[:10]

        for resource in resources:
            resource.rating = get_resource_rating(resource.id)

        context['resources'] = resources

    return render(request, 'uploader/leaderboard.html', context)


def licences(request):
    context = {'licences': Licence.objects.all()}
    return render(request, 'uploader/licences.html', context)


def notes_d(request, slug):
    return notes(request, None, None, None, None, slug)


@login_required
@permission_required(
    'notes.can_edit', '/denied?msg=For editing rights, please email contact@eduresourc.es')
def notes(request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    notes = Note.objects.filter(unit_topic=unit_topic)

    if notes.count() > 0:
        note = notes[0]
    else:
        note = None

    form = NotesForm(request.POST or None, instance=note or None,
                     label_suffix='')

    if request.method == 'POST':
        if not note:
            note = form.save(commit=False)
            note.unit_topic = unit_topic

            # sort slug
            unit = unit_topic.unit
            potential_slug = unit_topic.slug
            slugs = Note.objects.filter(slug__startswith=potential_slug)
            num_slugs = slugs.count()

            if num_slugs > 0:
                note.slug = unit_topic.unit.slug + '-' + str(num_slugs + 1)
            else:
                note.slug = potential_slug

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('uploader:view_notes',
                                                args=[subject_slug, exam_slug, syllabus_slug, unit_slug,
                                                      unit_topic.slug]))
    else:
        return render(request, "uploader/add_notes.html",
                      {'form': form, 'unit_topic': unit_topic})


def view_notes_d(request, slug):
    return view_notes(request, None, None, None, None, slug)


def view_notes(request, subject_slug, exam_slug, syllabus_slug, unit_slug,
               slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    notes_list = Note.objects.filter(unit_topic=unit_topic)
    notes = None
    if notes_list.count() > 0:
        notes = notes_list[0]
        rendered_text = render_markdown(notes.content)
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
        image = form.save()
        # FIXME
        return HttpResponseRedirect(
            reverse('uploader:view_image', args=[image.id]))

    return render(request, 'uploader/upload_image.html', {'form': form})


@login_required
def view_image(request, image_id):
    image = get_object_or_404(Image, pk=image_id)
    return render(request, 'uploader/image.html', {'url': image.image.url})


@login_required
@user_passes_test(is_teacher, login_url='/denied')
def questions(
        request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
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


def question(request, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
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
        try:
            g = Group.objects.get(code=request.POST['group_code'])
            s = form.save()
            StudentGroup(group=g, student=s.studentprofile).save()
            messages.success(
                request,
                "Thanks for registering. You are now logged in.")
            new_user = authenticate(username=request.POST['username'],
                                    password=request.POST['password'])
            #new_user.groups.add(Group.objects.get(name='student'))
            login(request, new_user)
            return HttpResponseRedirect('/')
        except ObjectDoesNotExist:
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
            g.code = group_code()
            g.save()
            return HttpResponseRedirect(reverse('uploader:groups_list'))
    else:
        form = GroupForm(instance=group)

    return render(request, 'uploader/add_group.html', {'form': form})


@login_required
def group(request, slug):
    group = get_object_or_404(Group, slug=slug)
    student_group = StudentGroup.objects.filter(group=group)
    tests = Test.objects.filter(teacher=request.user).order_by('-pub_date')
    lessons = GroupLesson.objects.filter(group=group)

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
               'lessons': lessons}

    return render(request, 'uploader/group.html', context)


@login_required
def add_test(request):
    form = TestForm(request.POST or None)
    form.fields['group'].queryset = Group.objects.filter(teacher=request.user)

    if request.POST:
        if form.is_valid():
            subject = get_object_or_404(Subject, pk=request.POST['subject'])
            group = get_object_or_404(Group, pk=request.POST['group'])
            code = random_key(4, 'Test')

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
    return link_resource(request, 'test', code)
    
    
def lesson_present(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    lis = LessonItem.objects.filter(lesson=lesson)
    context = {'lesson': lesson, 'lis': lis}
    return render(request, 'uploader/lesson_present.html', context)


def denied(request):
    msg = request.GET['msg']
    return render(request, 'uploader/permission_denied.html', {'msg': msg})

"""
ajax views
"""


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


def rate(request, resource_id, rating):
    """just silently ignore non-logged in ratings
    """
    if request.user.is_authenticated():
        _rating = Rating()
        _rating.user = request.user
        _rating.resource = get_object_or_404(Resource, pk=resource_id)
        _rating.rating = rating

        try:
            _rating.save()
            score_points(request.user.id, "Rate")
        except IntegrityError as e:
            # silently ignore duplicate votes
            pass

    return HttpResponse('')


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