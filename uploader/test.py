from os.path import abspath, join, dirname
from shutil import rmtree
from tempfile import mkdtemp

from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
import mock

