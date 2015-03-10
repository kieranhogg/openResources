""" 
openTeach related settings
"""
SITE_NAME = 'openTeach'
APP_VERSION = "0.1 beta"

"""
Django settings
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'templates'),)

TEMPLATE_CONTEXT_PROCESSORS = (
    # Required by allauth template tags
    "django.core.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.contrib.messages.context_processors.messages",
    # allauth specific context processors
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
    'openteach.context_processors.global_settings',
    "django.core.context_processors.media",
    "django.core.context_processors.static",
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'


AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",

    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

ALLOWED_HOSTS = []
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

AUTH_PROFILE_MODULE = 'accounts.UserProfile'

# Application definition

INSTALLED_APPS = (
    'suit',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'uploader',
    'storages',
    'openteach',
    'django_gravatar',
    'allauth',
    'allauth.account',
    #'allauth.socialaccount',
    'jquery',
    # ... include the providers you want to enable:
    #'allauth.socialaccount.providers.facebook',
    #'allauth.socialaccount.providers.github',
    #'allauth.socialaccount.providers.google',
    #'allauth.socialaccount.providers.stackexchange',
    #'allauth.socialaccount.providers.twitter',
    #'allauth.socialaccount.providers.openid',
    'micawber.contrib.mcdjango',
    
)
MICAWBER_PROVIDERS = 'micawber.contrib.mcdjango.providers.bootstrap_embedly'
# Allauth
SITE_ID = 1

REGISTRATION_OPEN = True                # If True, users can register
# ACCOUNT_SIGNUP_FORM_CLASS = 'uploader.forms.SignupForm'
ACCOUNT_ACTIVATION_DAYS = 7     # One-week activation window; you may, of course, use a different value.
REGISTRATION_AUTO_LOGIN = True  # If True, the user will be automatically logged in.
LOGIN_REDIRECT_URL = '/'  # The page you want users to arrive at after they successful log in
LOGIN_URL = '/accounts/login/'  # The page users are directed to if they are not logged in,
                                                                # and are trying to access pages requiring authentication

UPLOAD_FILE_TYPES = ['pdf', 'vnd.oasis.opendocument.text','vnd.ms-excel','msword','application/vnd.openxmlformats-officedocument.presentationml.presentation',]
UPLOAD_FILE_MAX_SIZE = 52428800 # 50mb



MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'openteach.urls'

WSGI_APPLICATION = 'openteach.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
try:
    from local_settings import *
except ImportError:
    pass

assert len(SECRET_KEY) > 20, 'Please set SECRET_KEY in local_settings.py'
