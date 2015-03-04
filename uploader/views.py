import re
import requests
from django.shortcuts import (render, get_object_or_404, get_list_or_404, 
    render_to_response, redirect)
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.template import RequestContext, loader
from uploader.models import (Subject, ExamLevel, Syllabus, Resource, Unit, File, 
    Rating, UnitTopic, Message, UserProfile, Licence, Note, Bookmark, Image)
from uploader.forms import (BookmarkStageOneForm, FileStageOneForm, 
    ResourceStageTwoForm, NotesForm, ImageForm)
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
from django.utils.text import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required


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
def resource(request, slug):
    resource = get_object_or_404(Resource, slug=slug)
    
    if resource.file is not None:
        # FIXME remove?
        pattern = '\%user_link%:[\d]+'
        # should hopefully never need the 'or's here but better than dying
        if re.match(pattern, resource.file.author_link or "") is not None:
            user_id = resource.file.author_link.split(":")[1]
            # FIXME use var
            resource.file.author_link = '/profile/' + user_id
    
    context = {
        'resource': resource, 
        'rating': get_resource_rating(resource.id),
        'rating_val': get_resource_rating(resource.id, 'values')
    }
    return render_to_response('uploader/resource_view.html', 
        context_instance=RequestContext(request, context))

# Calculate a resource's rating
def get_resource_rating(resource_id, use='display'):
    ratings = Rating.objects.filter(resource__id = resource_id)
    # TODO hide < a certain number too?
    if len(ratings) == 0:
        if use == 'values':
            return 0
        else:
            return "No rating yet"
    else:
        total = 0
        count = 0
        for rating in ratings:
            total = total + rating.rating
            count = count + 1
        return float(total) / float(count)

def add_file(request):
    form = FileStageOneForm(
        request.POST or None, 
        request.FILES or None,
        label_suffix='',
        initial={'uploader': request.user}
    )
    
    # If we've received a submitted form
    if request.method == 'POST' and form.is_valid():
        file = form.save(commit=False)
        
        # set excluded fields
        file.filesize = request.FILES['file'].size
        file.filename = request.FILES['file'].name
        file.mimetype = request.FILES['file'].content_type
        file.uploader = request.user
        file.slug = slugify(file.title)
        
        # check author fields
        if 'i_am_the_author' in request.POST and request.POST['i_am_the_author'] == 'on':
            file.author = str(request.user)
            # FIXME
            file.author_link = "/profile/" + request.user.username

        _file = form.save()

        # save the file_id in session to pass to the next stage
        # TODO is there a cleaner way than this?
        # we run the risk of orphaned files without resources
        request.session['_file_id'] = _file.id
        return HttpResponseRedirect('stage_two')
    else:
        return render(request, "uploader/resource_add_file.html", {'form': form})

def add_bookmark(request):
    form = BookmarkStageOneForm(
        request.POST or None, 
        label_suffix='',
        initial={'uploader': request.user}
    )
    
    # If we've received a submitted form
    if request.method == 'POST':
        if form.is_valid():
            bookmark = form.save(commit=False)
            bookmark.slug = slugify(bookmark.title)
            form.save()
            request.session['_bookmark_id'] = bookmark.id
            return HttpResponseRedirect('stage_two')
        else:
            return render(
                request, 
                "uploader/resource_add_bookmark.html", 
                {'form': form}
            )
        
    # no form submitted, show form
    else:
        return render(request, "uploader/resource_add_bookmark.html", {'form': form})


def add_resource(request):
    return render(request, "uploader/resource_add.html")

def link_file(request, slug):
    file = get_object_or_404(File, slug=slug)
    return add_resource_stage_two(request, file.id)
    
def link_bookmark(request, slug):
    bookmark = get_object_or_404(Bookmark, slug=slug)
    return add_resource_stage_two(request, None, bookmark.id)

def add_resource_stage_two(request, _file_id=None, _bookmark_id=None):
    bookmark_id = None
    file_id = None
    slug = None

    if request.method == 'GET':
        # get the link or file
            
        if _file_id is not None:
            file_id = _file_id
        elif request.session.get('_file_id') is not None:
            file_id = request.session.get('_file_id')
        elif _bookmark_id is not None:
            bookmark_id = _bookmark_id
        elif request.session.get('_bookmark_id') is not None:
            bookmark_id = request.session.get('_bookmark_id')    
        else:
            raise Http404
        
        request.session['_bookmark_id'] = None
        request.session['_file_id'] = None
    
    # create and save
    form = ResourceStageTwoForm(
        request.POST or None, 
        request.FILES or None,
        initial={
            'bookmark': bookmark_id, 
            'file': file_id, 
            'uploader': request.user
        },
        label_suffix=''
    )   
    
    if request.method == 'POST' and form.is_valid():
        resource = form.save(commit = False)
        
        #work out slug
        if resource.file is not None:
            resource.slug = resource.file.slug
        else:
            resource.slug = resource.bookmark.slug
            
        # check if we already have one with that name, append number if so
        num_results = Resource.objects.filter(
            slug__startswith=resource.slug).count()
        if num_results > 0:
            append = num_results + 1
            resource.slug += '-' + str(append)
        
        if request.user.is_authenticated():
            # if we're logged in auto-approve
            resource.approved = True
            form.save()
            score_points(request.user, "Add Resource")

        return redirect("/?s=1")
    
    return render(request, "uploader/resource_add_stage_two.html", {'form': form})
    
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
        user_id = request.user.id
        #
    # /profile/ and not logged in
    elif username == None and not request.user.is_authenticated():
        return HttpResponse("Not logged in")
    # /profile/1
    else:
        True
    return render(request, 'uploader/profile.html', {})

@login_required
def user_resources(request, user_id=None):
    resources = Resource.objects.filter(uploader=request.user)
    
    # TODO this could get slow if the user has a lot of resources, maybe store
    # on the resource table after each rating?
    for resource in resources:
        resource.rating = get_resource_rating(resource.id)
    return render(request, 'uploader/user_resources.html', {'resources': resources})
    
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
        note = form.save(commit=False)
        note.unit_topic = unit_topic

        # sort slug
        unit = unit_topic.unit
        potential_slug = unit_topic.slug
        note_exists = bool(Note.objects.filter(pk=note.id).count())
        check_slug = Note.objects.filter(slug=slug).count()
        
        if not note_exists and check_slug > 0:
            note.slug = unit_topic.unit.slug + '-' + unit_topic.slug
        elif not note_exists:
            note.slug = potential_slug

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('uploader:view_notes', 
            args=[subject_slug, exam_slug, syllabus_slug, unit_slug, 
                  unit_topic.slug]))
    else:
        return render(request, "uploader/notes_add.html", {'form': form, 'unit_topic': unit_topic })
        
def view_notes(request, subject_slug, exam_slug, syllabus_slug, unit_slug, slug):
    unit_topic = get_object_or_404(UnitTopic, slug=slug)
    notes_list = Note.objects.filter(unit_topic=unit_topic)
    notes = None
    if notes_list.count() > 0:
        notes = notes_list[0]
        headers = {'Content-Type': 'text/plain'}
        #data = notes.content.encode('utf-8')
        data = None
        if type(notes.content) == bytes:  # sometimes body is str sometimes bytes...
            data = notes.content
        else:
            data = notes.content.encode('utf-8')
        
        r = requests.post('https://api.github.com/markdown/raw', headers=headers, data=data)
        notes.content = r.text.encode('utf-8')

    context =  {'notes': notes, 'unit_topic': unit_topic}
    return render(request, 'uploader/notes.html', context)

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
        return redirect('/image/' + str(image.id))

    return render(request, 'uploader/upload_image.html', {'form': form})

@login_required    
def view_image(request, image_id):
    image = get_object_or_404(Image, pk=image_id)
    return render(request, 'uploader/image.html', {'url': image.image.url})
    
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
