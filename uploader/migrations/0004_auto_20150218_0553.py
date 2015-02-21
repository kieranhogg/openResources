# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0003_exam_exam_board'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='exam_level',
            field=models.ForeignKey(default=1, to='uploader.ExamLevel'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='exam',
            name='subject',
            field=models.ForeignKey(to='uploader.Subject'),
            preserve_default=True,
        ),
    ]
