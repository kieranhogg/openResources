from django.conf import settings
from uploader.models import Message
 
def global_settings(request):
    # return any necessary values
    return {
        'SITE_NAME': settings.SITE_NAME,
        'APP_VERSION': settings.APP_VERSION
    }
    
def messages(request):
    return {
        'messages': Message.objects.filter(),
    }