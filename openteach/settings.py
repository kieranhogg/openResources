""" 
openTeach related settings
"""
SITE_NAME = 'openTeach'
APP_VERSION = "0.7"

"""
Django settings
"""

# Build paths inside the project like this: os.path.join(BASE_DIR,', #...)
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

ALLOWED_HOSTS = []
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = (
    # 'grappelli',
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
    'jquery',
    'micawber.contrib.mcdjango',
    'bootstrapform',
    'bootstrap3_datetime',
    # haystack called at the bottom of the file
)

MICAWBER_PROVIDERS = 'micawber.contrib.mcdjango.providers.bootstrap_embedly'

# Allauth
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_USERNAME_BLACKLIST = ['admin']
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
REGISTRATION_OPEN = True
ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_AUTO_LOGIN = True
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/'

CONTENT_TYPES = ['application/pdf', 
                'vnd.oasis.opendocument.text',
                'vnd.ms-excel',
                'application/msword',
                'application/excel',
                'application/mspowerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'image/gif',
                'image/png',
                'image/jpg'
]

# files that can be embedded
# https://developers.box.com/view/#filetypes 18/04/15
PREVIEW_CONTENT_TYPES = ['application/pdf',
    'application/msword', #.doc	
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', #.docx	
    'application/vnd.ms-powerpoint', #.ppt	
    'application/vnd.openxmlformats-officedocument.presentationml.presentation', #.pptx	
    'application/vnd.ms-excel', #.xls	
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', #.xlsx	
    'text/plain', #.txt	
    'application/x-python', #.py
    'text/x-python', #.py
    'text/x-script.python', #.py
    'text/javascript', #.js	
    'application/x-javascript', #.js
    'application/javascript', #.js	
    'text/xml', #.xml	
    'application/xml', #.xml	
    'text/html', #.html
    'text/css', #.css
    'text/x-markdown', #.md	
    'text/x-script.perl', #.pl
    'text/x-c', #.c	
    'text/x-m', #.m
    'application/json' #.json
    ]

                    
MAX_UPLOAD_SIZE = 52428800 # 50mb


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

LANGUAGE_CODE = 'en-gb'
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

if not DEBUG:
    INSTALLED_APPS += ('haystack',)
    
assert len(SECRET_KEY) > 20, 'Please set SECRET_KEY in local_settings.py'
