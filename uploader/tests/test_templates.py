from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

class PageResponseTests(TestCase):

    def setUp(self):
        self.c = Client()

    def test_entries_access(self):
        response = self.c.get(reverse('uploader:index'))
        self.assertEqual(response.status_code, 200)