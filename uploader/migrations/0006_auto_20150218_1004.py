# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0005_auto_20150218_0603'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Exam',
            new_name='Syllabus',
        ),
    ]
