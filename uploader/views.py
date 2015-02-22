from django.shortcuts import (render, get_object_or_404, get_list_or_404, 
    render_to_response, redirect)
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from uploader.models import (Subject, ExamLevel, Syllabus, Resource, Unit, File, 
    Rating, UnitTopic, Message)
from uploader.forms import ResourceStageOneForm, ResourceStageTwoForm
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.contrib import messages

# Homepage view, shows subjects
def index(request):
    subjects = Subject.objects.filter(active=1)
    # get messages
    messages = Message.objects.filter()
    context = {
        'subjects': subjects,
        'messages': messages
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
    resources = Resource.objects.filter(unittopic__id = unit_topic_id)
    unit_topic = get_object_or_404(UnitTopic, pk=unit_topic_id)
    context = {
        'resources': resources, 
        'unit_topic': unit_topic,
    }
    return render(request, 'uploader/unit_topic.html', context)
    
# A single resource view
def resource(request, resource_id, slug=None):
    resource = get_object_or_404(Resource, pk=resource_id)
    context = {'resource': resource, 'rating': get_resource_rating(resource_id)}
    return render(request, 'uploader/resource_view.html', context)

# Calculate a resource's rating
def get_resource_rating(resource_id):
    ratings = Rating.objects.filter(resource__id = resource_id)
    # TODO hide < a certain number too?
    if len(ratings) == 0:
        return "No rating yet"
    else:
        total = 0
        count = 0
        for rating in ratings:
            total = total + rating.rating
            count = count + 1
        return float(total) / float(count)
    
def new_resource_blank(request):
    return new_resource(request, -1)
    
# def new_resource(request, syllabus_id):
#     # must be logged in
#     if not request.user.is_authenticated():
#         return redirect('/accounts/login/?next=%s' % request.path)
#     ResourceFormSet = modelformset_factory(Resource, ResourceForm)
#     if (syllabus_id != -1):
#         syllabus = get_object_or_404(Syllabus, pk=syllabus_id)
#     else:
#         syllabus = None
#     if request.method == 'POST':
#         formset = ResourceFormSet(request.POST, request.FILES)
#         if formset.is_valid():
#             formset.save(commit=True)
#         else:
#             context = {'form': formset}
#     else:
#         formset = ResourceFormSet(queryset=Resource.objects.none())
#     context = {"formset": formset, 'syllabus': syllabus, 
#             'url': request.path, 'syllabus_id': syllabus_id}
#     return render(request, "uploader/new_resource.html", context)

# TODO
def profile(request, user_id=None):
    # /profile/ and logged in
    if user_id == None and request.user.is_authenticated():
        user_id = request.user.id
        return HttpResponse("Own profile")
    # /profile/ and not logged in
    elif user_id == None and not request.user.is_authenticated():
        return HttpResponse("Not logged in")
    # /profile/1
    else:
        return HttpResponse("User profile")
        
def new_resource(request):
    form = ResourceStageOneForm(
        request.POST or None, 
        request.FILES or None,
        label_suffix=''
    )
    
    # If we've received a submitted form
    if request.method == 'POST':
        
        # if we have both
        if request.POST.get('link') != None and request.FILES.get('file') != None:
            form.add_error(None, "You must either add a link or a file, " + 
                "not both")
            return render(
                request, 
                "uploader/resource_add.html", 
                {'form': form}
            )
        
        # if there's just a file
        elif request.FILES.get('file') != None:
            # process file
            file = request.FILES['file']
            new_file = File(
                file=request.FILES['file'], 
                filename=file.name,
                mimetype=file.content_type,
                filesize=file.size
            )
            new_file.save()
            
            # save the file_id in session to pass to the next stage
            # TODO is there a cleaner way than this?
            # we run the risk of orphaned files without resources
            request.session['_file_id'] = new_file.id
            return HttpResponseRedirect('stage_two')

    
        # if there's just a link
        # FIXME for reason link is getting set but to blank,
        # == None is False, == "" is False so we're checking length as a hack
        elif len(request.POST.get('link')) > 0:
            request.session['_link'] = request.POST['link']
            return HttpResponseRedirect('stage_two')

        # neither
        else:
            form.add_error(None, "You must either add a link or a file")
            return render(
                request, 
                "uploader/resource_add.html", 
                {'form': form}
            )
        
    # no form submitted, show form
    else:
        return render(request, "uploader/resource_add.html", {'form': form})

    
def new_resource_stage_two(request):
    
    # get the link or file
    link = request.session.get('_link')
    file_id = request.session.get('_file_id')
    
    request.session['_link'] = None
    request.session['_file_id'] = None
    
    # create and save
    form = ResourceStageTwoForm(
        request.POST or None, 
        request.FILES or None,
        initial={'link': link, 'file': file_id},
        label_suffix=''
    )
    if request.method == 'POST':
        if form.is_valid():
            form.save(commit = True)
            messages.success(request, 'Resource added, thank you!')
            return redirect("/uploader/")
    
    return render(request, "uploader/resource_add_stage_two.html", {'form': form})