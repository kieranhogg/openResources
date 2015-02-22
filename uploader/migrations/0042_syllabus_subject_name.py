# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0041_auto_20150222_0451'),
    ]

    operations = [
        migrations.AddField(
            model_name='syllabus',
            name='subject_name',
            field=models.CharField(help_text=b'If the subject name is as above, leave blank otherwise enter correct name, e.g. Computing or Further Maths', max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
    ]
