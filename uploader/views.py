from django.shortcuts import (render, get_object_or_404, get_list_or_404, 
    render_to_response, redirect)
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from uploader.models import (Subject, ExamLevel, Syllabus, Resource, Unit, File, 
    Rating)
from uploader.forms import ResourceForm
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory

# Homepage view, shows subject
def index(request):
    subjects = Subject.objects.filter(active=1)
    context = {'subjects': subjects}
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
    resources = Resource.objects.filter(unit__id = unit_id)
    unit = get_object_or_404(Unit, pk=unit_id)
    context = {'resources': resources, 'unit': unit}
    return render(request, 'uploader/unit.html', context)
    
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
    
def new_resource(request, syllabus_id=None):
    # must be logged in
    if not request.user.is_authenticated():
        return redirect('/accounts/login/?next=%s' % request.path)
    form = ResourceForm(data=request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        form.instance.file = File.objects.get_or_create(request.FILES['file'])
        form.save(commit=True)
        # if form.is_valid():
        # instance = File(file=request.FILES['file'])
        # instance.filename = request.FILES['file'].filename
        # instance.mimetype = request.FILES['file'].
        # instance.save()
        # form.file = instance
        # form.save(commit=True)
            #process
        return redirect('/uploader/')

    return render(request, "uploader/new_resource.html", {'form': form})
    
def manage_resource(request, syllabus_id):
    ResourceFormSet = modelformset_factory(Resource)
    if request.method == 'POST':
        formset = ResourceFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save(commit=True)
            # do something.
    else:
        formset = ResourceFormSet()
    return render_to_response("uploader/new_resource.html", {
        "formset": formset,
    })
    
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