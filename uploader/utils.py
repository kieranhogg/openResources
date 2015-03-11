import requests, json
from django.utils.text import slugify
from django.conf import settings


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
