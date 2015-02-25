import re
from django.shortcuts import (render, get_object_or_404, get_list_or_404, 
    render_to_response, redirect)
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import RequestContext, loader
from uploader.models import (Subject, ExamLevel, Syllabus, Resource, Unit, File, 
    Rating, UnitTopic, Message, UserProfile, Licence)
from uploader.forms import (BookmarkStageOneForm, FileStageOneForm, 
    ResourceStageTwoForm)
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.models import User


# Homepage view, shows subjects
def index(request):
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
def subject(request, subject_id, slug=None):
    subject = get_object_or_404(Subject, pk=subject_id)
    # Sort by country first to enable grouping
    exam_levels = ExamLevel.objects.order_by('country', 'level_number')
    context = {'exam_levels': exam_levels, 'subject': subject}
    return render(request, 'uploader/subject_view.html', context)
    
# View list of syllabuses for a subject and level, e.g. {AQA, OCR} GCSE Maths 
# FIXME slug2, bit ugly
def syllabuses(request, subject_id, slug, exam_level_id, slug2=None):
    syllabus_list = Syllabus.objects.filter(
        subject = subject_id, 
        exam_level = exam_level_id
    )
    subject = get_object_or_404(Subject, pk=subject_id)
    level = get_object_or_404(ExamLevel, pk=exam_level_id)
    context = {
        'syllabus_list': syllabus_list, 
        'subject': subject,
        'level': level
    }
    return render(request, 'uploader/syllabus_index.html', context)
    
# Show one syllabuses page, has units on
def syllabus(request, syllabus_id, slug=None):
    syllabus = get_object_or_404(Syllabus, pk=syllabus_id)
    units = Unit.objects.filter(syllabus__id=syllabus_id)
    context = {'syllabus': syllabus, 'units': units}
    return render(request, 'uploader/syllabus.html', context)

# A single unit view
def unit(request, unit_id, slug=None):
    #resources = Resource.objects.filter(unit__id = unit_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    unit_topics = UnitTopic.objects.filter(unit__id = unit_id)
    context = {
        #'resources': resources, 
        'unit': unit,
        'unit_topics': unit_topics,
    }
    return render(request, 'uploader/unit.html', context)
    
def unit_topic(request, unit_topic_id, slug = None):
    _unit_topic_id = unit_topic_id
    resources = Resource.objects.filter(unit_topic_id = _unit_topic_id)
    unit_topic = get_object_or_404(UnitTopic, pk=unit_topic_id)
    context = {
        'resources': resources, 
        'unit_topic': unit_topic,
    }
    return render(request, 'uploader/unit_topic.html', context)
    
# A single resource view
def resource(request, resource_id, slug=None):
    resource = get_object_or_404(Resource, pk=resource_id)
    
    # fix user link
    pattern = '\%user_link%:[\d]+'
    if(re.match(pattern, resource.file.author_link)):
        user_id = resource.file.author_link.split(":")[1]
        # FIXME use var
        resource.file.author_link = '/profile/' + user_id
    
    context = {
        'resource': resource, 
        'rating': get_resource_rating(resource_id),
        'rating_val': get_resource_rating(resource_id, 'value')
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
        
        # check author fields
        if request.POST['i_am_the_author'] == 'on':
            file.author = str(request.user)
            file.author_link = '%user_link%:' + str(request.user.id)

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
            bookmark = form.save(commit=True)
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

    
def add_resource_stage_two(request):
    # temp_form = ResourceStageTwoForm(request.POST)
    # unit = request.POST.get('unit')
    # temp_form.fields['unit'].choices = [(unit, unit)]
    
    # get the link or file
    bookmark_id = request.session.get('_bookmark_id')
    file_id = request.session.get('_file_id')
    
    request.session['_link'] = None
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

        if request.user.is_authenticated():
            # if we're logged in auto-approve
            resource.approved = True
            
            form.save()
            score_points(request.user, "Add Resource")
            messages.success(request, 'Resource added, thank you!')

        return redirect("/uploader/")
    
    return render(request, "uploader/resource_add_stage_two.html", {'form': form})
    
def score_points(user, action):
    points = {
        "Add Resource": 25,
        "Vote": 1
    }
    user_profile = UserProfile.objects.get(user = user.id)
    user_profile.score += points[action]
    user_profile.save()
    
    
# TODO
def profile(request, user_id=None):
    # /profile/ and logged in
    if user_id == None and request.user.is_authenticated():
        user_id = request.user.id
        #
    # /profile/ and not logged in
    elif user_id == None and not request.user.is_authenticated():
        return HttpResponse("Not logged in")
    # /profile/1
    else:
        True
    return render(request, 'uploader/profile.html', {})
        
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
    
def rate(request, resource_id, rating):
    if request.user.is_authenticated():
        _rating = Rating()
        _rating.user = request.user
        _rating.resource = get_object_or_404(Resource, pk=resource_id)
        _rating.rating = rating
        
        try:
            _rating.save()
        except IntegrityError as e:
            # silently ignore duplicate votes
            pass
    
    return HttpResponse('')