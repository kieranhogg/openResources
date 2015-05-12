import requests, json, shutil, os, random, string, urllib
from tempfile import NamedTemporaryFile
from django.utils.text import slugify
from django.conf import settings
from django.core.files.base import File as DjangoFile
from django.conf import settings
from django.http import (HttpResponse, HttpResponseRedirect, JsonResponse, 
    Http404, HttpResponseForbidden)
import markdown
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
    # headers = {'Content-Type': 'text/plain'}
    # #data = notes.content.encode('utf-8')
    # data = None
    # if type(text) == bytes:  # sometimes body is str sometimes bytes...
    #     data = text
    # else:
    #     data = text.encode('utf-8')
    
    # url = None
    # #if len(settings.GITHUB_CLIENT_SECRET) == 40 and len(settings.GITHUB_CLIENT_ID) == 20:
    # url = ('https://api.github.com/markdown/raw?clientid=' + 
    #       settings.GITHUB_CLIENT_ID + "&client_secret=" + 
    #       settings.GITHUB_CLIENT_SECRET)
    # #else:
    # #    url = 'https://api.github.com/markdown/raw'

    # r = requests.post(url, headers=headers, data=data)
    # return r.text.encode('utf-8')
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
    
def get_resource_rating(resource_id, use='display'):
    """Calculate a resource's rating
    """
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


def random_key(length, item=None):
    unique = False
    
    while not unique:
        key = ''
        for i in range(length):
            key += random.choice(string.lowercase + string.digits)
        if not item:
            unique = True
        else:
            if item == 'Test':
                if Test.objects.filter(code=key).count() == 0:
                    unique = True
            elif item == 'Assignment':
                if Assignment.objects.filter(code=key).count() == 0:
                    unique = True
            elif item == 'Lesson':
                if Lesson.objects.filter(code=key).count() == 0:
                    unique = True
            elif item == 'Resource':
                if Resource.objects.filter(code=key).count() == 0:
                    unique = True
            else:
                raise Exception('Type not implemented')

    return key
    
    
def group_code():
    # TODO check DB
    # a length of 3 gives us: 238328 codes
    return random_key(3)


def extract(url):
    """extracts information from a URL using embed.ly API
    """
    # url = urllib.unquote(encoded_url).decode('utf8')
    api_url = "http://api.embed.ly/1/extract?key=" + settings.MICAWBER_EMBEDLY_KEY + "&url=" + url + "&maxwidth=500"
    r = requests.get(api_url)
    return json.loads(r.text)


def embed_resources(text):
    import re
    card_html = '<a class="embedly-card" href="%s">%s</a><script async src="//cdn.embedly.com/widgets/platform.js" charset="UTF-8"></script>'
    pattern = re.compile(r'\(resource\)\[([\da-z]{4}?)\]')
  
    for match in re.finditer(pattern, text):
        try:
            resource = Resource.objects.get(code=match.group(1))
            replace = card_html % (resource.bookmark.link, resource.bookmark.title)
            text = text.replace(match.group(0), replace)
        except Resource.DoesNotExist:
            pass
    return text
    

def get_screenshot(url):
    get_url = 'http://api.embed.ly/1/oembed?url=' + url + '&maxwidth=500&key=' + settings.MICAWBER_EMBEDLY_KEY
    r = requests.get(get_url)
    try:
        thumb = json.loads(r.text)['thumbnail_url']
    except ValueError:
        thumb = None
    
    return thumb
    

def get_embed(url):
    get_url = 'http://api.embed.ly/1/oembed?url=' + url + '&maxwidth=400&key=' + settings.MICAWBER_EMBEDLY_KEY
    r = requests.get(get_url)
    json = r.json()
    if 'html' in json:
        return json['html']
    else:
        return None
    

def get_embed_card(url):
    return '<a class="embedly-card" href="%s">Link</a><script async src="//cdn.embedly.com/widgets/platform.js" charset="UTF-8"></script>' % url
    