# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0002_examlevel_level_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='exam_board',
            field=models.ForeignKey(default=1, to='uploader.ExamBoard'),
            preserve_default=False,
        ),
    ]
