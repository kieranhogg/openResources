import re
import requests
from django.shortcuts import (render, get_object_or_404, get_list_or_404, 
    render_to_response, redirect)
from django.http import (HttpResponse, HttpResponseRedirect, JsonResponse, 
    Http404, HttpResponseForbidden)
from django.template import RequestContext, loader
from uploader.models import (Subject, ExamLevel, Syllabus, Resource, Unit, File, 
    Rating, UnitTopic, Message, UserProfile, Licence, Note, Bookmark, Image)
from uploader.forms import (BookmarkForm, FileForm, 
    LinkResourceForm, NotesForm, ImageForm)
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.views.generic.edit import UpdateView
from django.utils.text import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings


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
        file = File(uploader=request.user)

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
            
            return HttpResponseRedirect(redirect_url)
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
        bookmark = Bookmark(uploader=request.user)

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

    resource = Resource(uploader=request.user, file=file or None, 
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
                form.save()
                score_points(request.user, "Add Resource")
    
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
        
        url = None
        if len(settings.GITHUB_CLIENT_SECRET) == 40 and len(settings.GITHUB_CLIENT_ID) == 20:
            url = ('https://api.github.com/markdown/raw?clientid=' + 
                   settings.GITHUB_CLIENT_ID + "&client_secret=" + 
                   settings.GITHUB_CLIENT_SECRET)
        else:
            url = 'https://api.github.com/markdown/raw'

        r = requests.post(url, headers=headers, data=data)
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
        return HttpResponseRedirect(
            reverse('uploader:view_image', args=[image.id]))

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
