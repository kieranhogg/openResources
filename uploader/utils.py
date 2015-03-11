from django.utils.text import slugify

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
    