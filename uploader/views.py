import re
import requests
from django.shortcuts import (render, get_object_or_404, get_list_or_404, 
    render_to_response, redirect)
from django.http import (HttpResponse, HttpResponseRedirect, JsonResponse, 
    Http404, HttpResponseForbidden)
from django.template import RequestContext, loader
from uploader.models import (Subject, ExamLevel, Syllabus, Resource, Unit, File, 
    Rating, UnitTopic, Message, UserProfile, Licence, Note, Bookmark, Image,
    Question, MultipleChoiceQuestion, Answer, MultipleChoiceAnswer,
    MultipleChoiceUserAnswer, Lesson, LessonItem)
from uploader.forms import (BookmarkForm, FileForm, 
    LinkResourceForm, NotesForm, ImageForm, MultipleChoiceQuestionForm)
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
from django.utils.text import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import logging, json, time
logging.basicConfig()

logger = logging.getLogger(__name__)


# Homepage view, shows subjects
def index(request):
    if request.GET and request.GET['s'] == "1":
        messages.success(request, 'Resource added, thank you!')

    subjects = Subject.objects.filter(active=1)
    
    # get messages TODO use constants
    user_messages = Message.objects.filter(user_to=request.user.id)
    announce_messages = Message.objects.filter(type=2)
    sticky_messages = Message.objects.filter(type=3)

    context = {
        'subjects': subjects,
        'user_messages': user_messages | announce_messages | sticky_messages
    }
    return render(request, 'uploader/index.html', context)

# View one subject, shows exam levels, e.g. GCSE
def subject(request, slug):
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
    
def unit_resources(request, subject_slug, exam_slug, syllabus_slug, unit_slug):
    unit = get_object_or_404(Unit, slug=unit_slug)
    resources = Resource.objects.filter(
        unit__id=unit.id,
        unit_topic__isnull=True)

    context = {'unit': unit, 'resources': resources}
    return render(request, 'uploader/unit_resources.html', context)    

# View list of syllabuses for a subject and level, e.g. {AQA, OCR} GCSE Maths 
def syllabuses(request, subject_slug, exam_slug):
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
    
# Show one syllabuses page, has units on
def syllabus(request, subject_slug, exam_slug, slug):
    syllabus = get_object_or_404(Syllabus, slug=slug)
    units = Unit.objects.filter(syllabus__id=syllabus.id)
    context = {'syllabus': syllabus, 'units': units}
    return render(request, 'uploader/syllabus.html', context)

# A single unit view
def unit(request, subject_slug, exam_slug, syllabus_slug, slug):
    unit = get_object_or_404(Unit, slug=slug)
    unit_topics = UnitTopic.objects.filter(unit__id = unit.id).order_by(
            'section', 'pub_date')
    resources = None

    if unit_topics.count() == 0:
        resources = Resource.objects.filter(unit__id = unit.id)

    context = {
        'resources': resources, 
        'unit': unit,
        'unit_topics': unit_topics,
    }
    return render(request, 'uploader/unit.html', context)
    
def unit_topic(request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    notes = Note.objects.filter(unit_topic = unit_topic)

    resources = Resource.objects.filter(unit_topic_id = unit_topic.id)
    context = {
        'resources': resources, 
        'unit_topic': unit_topic,
        'notes': notes
    }
    return render(request, 'uploader/unit_topic.html', context)
    
# A single resource view
def view_resource(request, slug):
    resource = get_object_or_404(Resource, slug=slug)
    
    context = {
        'resource': resource, 
        'rating': get_resource_rating(resource.id),
        'rating_val': get_resource_rating(resource.id, 'values')
    }
    return render_to_response('uploader/resource_view.html', 
        context_instance=RequestContext(request, context))
        
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

# Calculate a resource's rating
def get_resource_rating(resource_id, use='display'):
    ratings = Rating.objects.filter(resource__id = resource_id)
    # TODO hide < a certain number too?
    if len(ratings) == 0:
        return 3.0
    else:
        total = 0
        count = 0
        for rating in ratings:
            total = total + rating.rating
            count = count + 1
        return float(total) / float(count)

def file(request, slug=None):
    if slug:
        file = get_object_or_404(File, slug=slug)

        if file.uploader != request.user and not request.user.is_superuser:
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
                
                # set excluded fields
                file.filesize = request.FILES['file'].size
                file.filename = request.FILES['file'].name
                file.mimetype = request.FILES['file'].content_type
                if request.user.is_authenticated():
                    file.uploader = request.user
                
                potential_slug = slugify(file.title)
                num_slugs = File.objects.filter(slug__startswith=potential_slug).count()
        
                if num_slugs > 0:
                    file.slug = potential_slug + '-' + str(num_slugs + 1)
                else:
                    file.slug = potential_slug
    
                form.save()
                return HttpResponseRedirect(
                    reverse('uploader:link_file', args=[file.slug]))
            else:
                form.save()
                return HttpResponseRedirect(reverse('uploader:user_files'))
    else:
        form = FileForm(instance=file)

    return render_to_response('uploader/add_file.html', {
        'form': form,
    }, context_instance=RequestContext(request))


def bookmark(request, slug=None):
    bookmark = None
    
    if slug:
        bookmark = get_object_or_404(Bookmark, slug=slug)
        if bookmark.uploader != request.user and not request.user.is_superuser:
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
                
                potential_slug = slugify(bookmark.title)
                num_slugs = Bookmark.objects.filter(slug__startswith=potential_slug).count()
        
                if num_slugs > 0:
                    bookmark.slug = potential_slug + '-' + str(num_slugs + 1)
                else:
                    bookmark.slug = potential_slug
                
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
    return link_resource(request, 'file', slug)
    
def link_bookmark(request, slug):
    bookmark = get_object_or_404(Bookmark, slug=slug)
    return link_resource(request, 'bookmark', slug)

def link_resource(request, type, slug):
    bookmark = None
    file = None

    if type == 'bookmark':
        bookmark = get_object_or_404(Bookmark, slug=slug)
    elif type == 'file':
        file = get_object_or_404(File, slug=slug)

    if request.user.is_authenticated():
        resource = Resource(uploader=request.user, file=file or None, 
                            bookmark=bookmark or None, approved=False)
    else:
        resource = Resource(file=file or None, 
                            bookmark=bookmark or None, approved=False)
                            
    if request.method == 'POST':
        form = LinkResourceForm(request.POST, instance=resource)
        if form.is_valid():
            resource = form.save(commit = False)
            #work out slug
            if resource.file is not None:
                resource.slug = resource.file.slug
            else:
                resource.slug = resource.bookmark.slug
                
            # check if we already have one with that name, append number if so
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
    
            return redirect("/?s=1")
    else:
        form = LinkResourceForm(instance=resource)

    return render_to_response('uploader/link_resource.html', {
        'form': form,
    }, context_instance=RequestContext(request))
    
def score_points(user, action):
    points = {
        "Add Resource": 25,
        "Rate": 1
    }
    user_profile = UserProfile.objects.get(user = user.id)
    user_profile.score += points[action]
    user_profile.save()
    
# TODO
def profile(request, username=None):
    # /profile/ and logged in
    if username == None and request.user.is_authenticated():
        user = request.user
        #
    # /profile/ and not logged in
    elif username == None and not request.user.is_authenticated():
        return HttpResponse("Not logged in")
    # /profile/1
    elif username:
        user = get_object_or_404(UserProfile, user__username=username)
    else:
        pass
    
    
    return render(request, 'uploader/profile.html', {})

@login_required
def user_resources(request, user_id=None):
    if not user_id:
        user_id = request.user
    resources = Resource.objects.filter(uploader=user_id)
    
    # TODO this could get slow if the user has a lot of resources, maybe store
    # on the resource table after each rating?
    for resource in resources:
        resource.rating = get_resource_rating(resource.id)
    return render(request, 'uploader/user_resources.html', {'resources': resources})
    
@login_required
def user_files(request, user_id=None):
    if not user_id:
        user_id = request.user
    files = File.objects.filter(uploader=user_id)
    for file in files:
        file.link_count = Resource.objects.filter(file=file).count()
    return render(request, 'uploader/user_resources.html', {'files': files})
    
@login_required
def user_bookmarks(request, user_id=None):
    bookmarks = Bookmark.objects.filter(uploader=request.user)
    for bookmark in bookmarks:
        bookmark.link_count = Resource.objects.filter(bookmark=bookmark).count()
    return render(request, 'uploader/user_resources.html', {'bookmarks': bookmarks})
    
@login_required
def user_questions(request, user_id=None):
    questions = MultipleChoiceQuestion.objects.filter(uploader=request.user)
    return render(request, 'uploader/user_resources.html', {'questions': questions})
    
# check that the lesson items aren't missing any values
def check_lesson_items(request, num_items):
    rp = request.POST
    for i in range(1, num_items + 1):
        _i = str(i)
        if not rp.get('order' + _i, None):
            return False    
    return True
        

@login_required
def user_lessons(request, user_id=None):
    form_errors = []
    
    if request.POST.get('submit', None):
        if request.POST.get('clear', None) == 'on':
            request.session['resources'] = None
            request.session['notes'] = None
            request.session['tests'] = None
            request.session['tasks'] = None
        elif request.POST['title']:
            form_errors.append('Please enter a lesson title')
        else:
            num_items = 0
            rs = request.session
            for types in ('resources', 'notes', 'tests', 'tasks'):
                if types in rs and rs[types]:
                    num_items += len(rs[types])
            
            # this check we've not missed an order number out
            items_okay = check_lesson_items(request, num_items)
            
            if num_items > 0 and items_okay:
                l = Lesson(title=request.POST['title'],
                            slug=slugify(request.POST['title']),
                            objectives=request.POST['objectives'],
                            uploader=request.user,
                        )
                url = request.build_absolute_uri(reverse('uploader:lesson', args=[slugify(request.POST['title'])]))
                post_url = 'https://www.googleapis.com/urlshortener/v1/url'
                payload = {'longUrl': url, 'key': "AIzaSyBS7z0dORE4qDwHND1"}
                headers = {'content-type': 'application/json'}
                r = requests.post(post_url, data=json.dumps(payload), headers=headers)
                data = r.json()
                l.url = data['id']
                l.save()
    
                rp = request.POST
                check_lesson_items(request, num_items)
                for i in range(1, num_items + 1):
                    _i = str(i)
                    li = LessonItem(
                        lesson=l,
                        type=rp.get('type' + _i, None),
                        slug=rp.get('slug' + _i, None),
                        order=rp.get('order' + _i, None),
                        instructions=rp.get('instructions' + _i, None),
                    )
                    
                    li.save()
                
                request.session['resources'] = None
                request.session['notes'] = None
                request.session['tests'] = None
                request.session['tasks'] = None
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            elif not items_okay:
                form_errors.append('Please add an order to all items')
    
    # check if we've got any stuff added to lesson
    resources = request.session.get('resources', None)
    resource_list = []
    if resources:
        count = 1
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
    
    lessons = Lesson.objects.filter(uploader=request.user)
    now = int(time.time())
    
    return render(request, 'uploader/user_lessons.html', 
        {'resources': resource_list, 'notes': notes_list, 
         'tests': tests_list, 'lessons': lessons, 'tasks': tasks_list, 
         'time': now, 'form_errors': form_errors})

def lesson(request, slug):
    l = get_object_or_404(Lesson, slug=slug)
    l.objectives = render_markdown(l.objectives)
    lis = LessonItem.objects.filter(lesson=l)
    for li in lis:
        if li.type == 'resources':
            r = get_object_or_404(Resource, slug=li.slug)
            if r.file:
                li.title = r.file.title
            else:
                li.title = r.bookmark.title
        elif li.type == 'notes' or li.type == 'test':
            li.title = get_object_or_404(UnitTopic, slug=li.slug).title
        elif li.type == 'task':
            pass

    return render(request, 'uploader/lesson.html', 
        {'lesson': l, 'lesson_items': lis})
        
def lesson_show(request, slug):
    l = get_object_or_404(Lesson, slug=slug)

    return render(request, 'uploader/lesson_show.html', 
        {'lesson': l})

def add_item_to_lesson(request, slug, type):
    
    if type == 'resource':
        resource = get_object_or_404(Resource, slug=slug)
        if resource:
            if 'resources' not in request.session or request.session['resources'] is None:
                request.session['resources'] = (slug,)
            elif slug not in request.session['resources']:
                request.session['resources'].append(slug)
            request.session.modified = True
            messages.error(request,"Horsey Bollox!")
    
    elif type == 'notes':
        unit_topic = get_object_or_404(UnitTopic, slug=slug)
        notes = get_object_or_404(Note, unit_topic=unit_topic)
        if notes:
            logger.error("saving: " + slug)
            logger.error("saving: " + str(notes.slug))
            logger.error("saving: " + str(unit_topic))
            if 'notes' not in request.session or request.session['notes'] is None:
                request.session['notes'] = (slug,)
            elif slug not in request.session['notes']:
                request.session['notes'].append(slug)
            request.session.modified = True

    elif type == 'test':
        unit_topic = get_object_or_404(UnitTopic, slug=slug)
        if request.session.get('tests', None) is None:
            request.session['tests'] = (slug,)
        elif slug not in request.session['tests']:
            request.session['tests'].append(slug)
        request.session.modified = True
        
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
        users = User.objects.filter().order_by('-userprofile__score')[:10]
        for user in users:
            user.resource_count = Resource.objects.filter(uploader=user).count()
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
def notes(request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    notes = Note.objects.filter(unit_topic=unit_topic)

    if notes.count() > 0:
        note = notes[0]
    else:
        note = None
    
    form = NotesForm(request.POST or None, instance=note or None, label_suffix='')

    if request.method == 'POST':
        if not note:
            note = form.save(commit=False)
            note.unit_topic = unit_topic
    
            # sort slug
            unit = unit_topic.unit
            potential_slug = unit_topic.slug
            num_slugs = Note.objects.filter(slug__startswith=potential_slug).count()
    
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
        return render(request, "uploader/add_notes.html", {'form': form, 'unit_topic': unit_topic })

def view_notes_d(request, slug):
    return view_notes(request, None, None, None, None, slug)
        
def view_notes(request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    notes_list = Note.objects.filter(unit_topic=unit_topic)
    notes = None
    if notes_list.count() > 0:
        notes = notes_list[0]
        rendered_text = render_markdown(notes.content)
        notes.content = rendered_text
    context =  {'notes': notes, 'unit_topic': unit_topic}
    return render(request, 'uploader/notes.html', context)
    
def render_markdown(text):
    headers = {'Content-Type': 'text/plain'}
    #data = notes.content.encode('utf-8')
    data = None
    if type(text) == bytes:  # sometimes body is str sometimes bytes...
        data = text
    else:
        data = text.encode('utf-8')
    
    url = None
    if len(settings.GITHUB_CLIENT_SECRET) == 40 and len(settings.GITHUB_CLIENT_ID) == 20:
        url = ('https://api.github.com/markdown/raw?clientid=' + 
               settings.GITHUB_CLIENT_ID + "&client_secret=" + 
               settings.GITHUB_CLIENT_SECRET)
    else:
        url = 'https://api.github.com/markdown/raw'

    r = requests.post(url, headers=headers, data=data)
    return r.text.encode('utf-8')

@login_required
def upload_image(request):
    form = ImageForm(
        request.POST or None, 
        request.FILES or None,
        label_suffix='',
        initial={'uploader': request.user} #FIXME initial
    )
    
    if request.method == 'POST' and form.is_valid():
        image = form.save()
        #FIXME
        return HttpResponseRedirect(
            reverse('uploader:view_image', args=[image.id]))

    return render(request, 'uploader/upload_image.html', {'form': form})

@login_required    
def view_image(request, image_id):
    image = get_object_or_404(Image, pk=image_id)
    return render(request, 'uploader/image.html', {'url': image.image.url})
    
def test(request, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    complete_count = 0
    question_count = 0
    questions = None
    
    if request.POST:
        score = 0
        
        for question_key in [key for key in request.POST.keys() if key.startswith('question')]:
            question_num = question_key.replace('question', '')
            question = get_object_or_404(MultipleChoiceQuestion, pk=question_num)
            answer_num = request.POST.get(question_key)
            answer = get_object_or_404(MultipleChoiceAnswer, 
                                      question=question, number=answer_num)

            answer = MultipleChoiceUserAnswer(
                question=question, 
                answer_chosen=answer,
                user=request.user)
            answer.save()

        return HttpResponseRedirect(
            reverse('uploader:test_feedback', args=[slug]))
    else:
        # student
        if request.user.is_authenticated() and request.user.userprofile.type == 1: 
            # try to find maximum ten questions that the user hasn't taken
            completed_qs = MultipleChoiceUserAnswer.objects.filter(user=request.user, question__unit_topic=unit_topic).values('question_id')
            complete_count = completed_qs.count()
            
            # FIXME random sorting could be more efficient
            questions = MultipleChoiceQuestion.objects.filter(unit_topic=unit_topic).exclude(id__in=completed_qs).order_by('?')[:10]
            question_count = MultipleChoiceQuestion.objects.filter(unit_topic=unit_topic).count()
            
            # FIXME think there's a function to do this
            for question in questions:
                answer_list = []
                answers = MultipleChoiceAnswer.objects.filter(question=question).order_by('number')
                for answer in answers:
                    answer_list.append(answer)
                
                question.answers = answer_list
        else:
            questions = MultipleChoiceQuestion.objects.filter(unit_topic=unit_topic)
            # FIXME think there's a function to do this
            for question in questions:
                answer_list = []
                answers = MultipleChoiceAnswer.objects.filter(question=question).order_by('number')
                for answer in answers:
                    answer_list.append(answer)
                
                question.answers = answer_list

    return render(request, 'uploader/test.html', 
    {'questions': questions, 'unit_topic': unit_topic, 
     'complete_count': complete_count, 'question_count': question_count})
    
def test_feedback(request, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    questions = MultipleChoiceQuestion.objects.filter(unit_topic=unit_topic)
    question_list = []
    for question in questions:
        user_answer = MultipleChoiceUserAnswer.objects.filter(question=question)
        if user_answer.count() == 1:
            question.answer = MultipleChoiceAnswer.objects.filter(question=question)[0]
            question.user_answer = user_answer
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
    
# ajax views


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
    unit_topics = UnitTopic.objects.filter(unit=unit)
    unit_topics_dict = {}
    for unit_topic in unit_topics:
        unit_topics_dict[unit_topic.id] = str(unit_topic)
    return JsonResponse(unit_topics_dict)

# just silently ignore non-logged in ratings
def rate(request, resource_id, rating):
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
