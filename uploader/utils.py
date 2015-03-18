import requests, json, shutil, os, random, string
from tempfile import NamedTemporaryFile
from django.utils.text import slugify
from django.conf import settings
from django.core.files.base import File as DjangoFile
from django.conf import settings
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
    duplicate is found
    """
    text = slugify(unicode(text))
    num_slugs = model.objects.filter(slug__startswith=text).count()
    
    if num_slugs > 0:
        text += '-' + str(num_slugs + 1)
    
    return text
    
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
    
def shorten_url(url): 
    post_url = 'https://www.googleapis.com/urlshortener/v1/url'
    payload = {'longUrl': url, 'key': settings.GOOGLE_URL_KEY}
    headers = {'content-type': 'application/json'}
    r = requests.post(post_url, data=json.dumps(payload), headers=headers)
    data = r.json()
    return data['id']
    
    
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


def random_key(length):
    key = ''
    for i in range(length):
        key += random.choice(string.lowercase + string.uppercase + string.digits)
    return key
    
    
def group_code():
    # TODO check DB
    # a length of 3 gives us: 238328 codes
    return random_key(3)