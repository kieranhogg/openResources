from django.utils import timezone
from uploader.utils import get_user_profile

class TimezoneMiddleware(object):
    def process_request(self, request):
        user_profile = get_user_profile(request.user)
        if user_profile and user_profile.timezone:
            timezone.activate(user_profile.timezone)