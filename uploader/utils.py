import requests, json, markdown, shutil, os, random, string, urllib
from tempfile import NamedTemporaryFile

from django.db.models.base import ModelBase
from django.conf import settings
from django.core.files.base import File as DjangoFile
from django.conf import settings
from django.http import (HttpResponse, HttpResponseRedirect, JsonResponse, 
    Http404, HttpResponseForbidden)
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from uploader.models import *


def screenshot(site):
    url = ('http://api.screenshotmachine.com/?key=68df53&size=M&url=' + site)
    response = requests.get(url, stream=True)
    with NamedTemporaryFile() as out_file:
        shutil.copyfileobj(response.raw, File(out_file))
    del response
    return out_file


def save_file(url):
    response = requests.get(url, stream=True)
    with NamedTemporaryFile() as out_file:
        shutil.copyfileobj(response.raw, DjangoFile(out_file))
    del response
    return DjangoFile(out_file)


def safe_slugify(text, model):
    """ Safely creates a slug using the given text and model. Check in the
    database to find duplicate slugs and appends an increasing number if a
    duplicate is found. Max length is 100
    """
    text = slugify(unicode(text))
    text = (text[:100]) if len(text) > 100 else text
    num_slugs = model.objects.filter(slug__startswith=text).count()
    
    if num_slugs > 0:
        text += '-' + str(num_slugs + 1)
    
    return text
    
def render_markdown(text):
    return markdown.markdown(text, extensions=['markdown.extensions.tables',
        'markdown.extensions.fenced_code', 'markdown.extensions.codehilite',
        'markdown.extensions.toc'])
    

def shorten_url(url):
    """Returns a short URL from tinyurl.com
    """
    get_url = 'http://tinyurl.com/api-create.php?url=%s' % url
    r = requests.get(get_url)
    return r.text

    
def shorten_lesson_url(request, group_code, lesson_code):
    local_url = request.build_absolute_uri(
        reverse('uploader:lesson', args=[group_code, lesson_code]))

    return shorten_url(local_url)


def generate_code(model=None, length=4):
    unique = False
    
    loops = 1
    while not unique:
        key = ''
        for i in range(length):
            key += random.choice(string.lowercase + string.digits)
        if not model:
            unique = True
        else:
            if type(model) is ModelBase:
                if model.objects.filter(code=key).count() == 0:
                    unique = True
            else:
                raise Exception('Not a valid model')
        
        loops += 1
        if loops > 10:
            raise Exception('Tried 10 codes for ' + str(model) + ' and stil not unique')

    return key
    

def extract(url):
    """extracts information from a URL using embed.ly API
    """
    # url = urllib.unquote(encoded_url).decode('utf8')
    api_url = "http://api.embed.ly/1/extract?key=" + settings.MICAWBER_EMBEDLY_KEY + "&url=" + url + "&maxwidth=500"
    r = requests.get(api_url)
    try:
        url = json.loads(r.text)
    except ValueError: # stops error emails when lookup times out
        url = None
    return url


def embed_resources(text):
    import re
    card_html = '<a class="embedly-card" href="%s">%s</a><script async src="//cdn.embedly.com/widgets/platform.js" charset="UTF-8"></script>'
    resource_pattern = re.compile(r'\@\[resource\]\(([\da-z]{4}?)\)')
    image_pattern = re.compile(r'\@\[image\]\(([\da-z]{4}?)\)')
    
    for match in re.finditer(resource_pattern, text):
        try:
            resource = Resource.objects.get(code=match.group(1))
            replace = card_html % (resource.bookmark.link, resource.bookmark.title)
            text = text.replace(match.group(0), replace)
        except Resource.DoesNotExist:
            pass
    return text
    

def get_screenshot(url):
    get_url = 'http://api.embed.ly/1/oembed?url=' + url + '&maxwidth=700&key=' + settings.MICAWBER_EMBEDLY_KEY
    r = requests.get(get_url)
    try:
        thumb = json.loads(r.text)['thumbnail_url']
    except (ValueError, KeyError):
        thumb = None
    
    return thumb
    

def get_embed(url):
    try:
        get_url = 'http://api.embed.ly/1/oembed?url=' + url + '&maxwidth=800&key=' + settings.MICAWBER_EMBEDLY_KEY
        r = requests.get(get_url)
        json = r.json()
        if 'html' in json:
            return json['html']
        else:
            return None
    except Exception: # eh, fuck it
        return None
    

def get_embed_card(url):
    return '<a class="embedly-card" href="%s">Link</a><script async src="//cdn.embedly.com/widgets/platform.js" charset="UTF-8"></script>' % url
    
    
def hierachy_from_slugs(subject_slug, exam_slug, syllabus_slug=None, unit_slug=None, slug=None):
    items = {}
    
    subject = get_object_or_404(Subject, slug=subject_slug)
    items['subject'] = subject
    
    exam_level = get_object_or_404(ExamLevel, slug=exam_slug)
    items['exam_level'] = exam_level
    
    if syllabus_slug:
        syllabus = get_object_or_404(Syllabus, slug=syllabus_slug, exam_level=exam_level, subject=subject)
        items['syllabus'] = syllabus
    
    if unit_slug:
        unit = get_object_or_404(Unit, slug=unit_slug, syllabus=syllabus)
        items['unit'] = unit
    
    if slug and unit_slug: 
        unit_topic = get_object_or_404(UnitTopic, slug=slug, unit=unit)
        items['unit_topic'] = unit_topic
        
    return items
    
    
def user_type(user):
    if not user.is_authenticated():
        return False
    elif hasattr(user, 'teacherprofile'):
        return 'teacher'
    elif hasattr(user, 'studentprofile'):
        return 'student'
    

def get_user_profile(user):
    if not user_type(user):
        return False
    elif user_type(user) == 'teacher':
        return user.teacherprofile
    elif user_type(user) == 'student':
        return user.studentprofile
    
    
    
class diff_object:
    import diff_match_patch as dmp
    text1 = None
    text2 = None
    diff = None
    patch = None

    def set_diff(self, text1, text2):
        text1 = text1
        text2 = text2
        diff = dmp.diff_main(text1, text2)
    
    
    def diff_to_html(self):
        if not diff:
            raise Exception("Please set a diff first")
        else:
            return diff_prettyHtml(diff)
            
    
    def set_patch(self, text1, text2):
        patch = dmp.patch_make(text1, text2)
        
    
    def patch_to_text(self):
        if not diff:
            raise Exception("Please set a patch first")
        else:
            return dmp.patch_toText(patch)
        
    
    def patch_to_html(self):
        if not diff:
            raise Exception("Please set a patch first")
        else:
            return dmp.path_toHtml(patch)
        
    
    def apply_patch(self, new_text):
        if not diff:
            raise Exception("Please set a patch first")
        else:
            return dmp.patch_apply(patch, new_text)
        