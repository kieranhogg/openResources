# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0035_auto_20150221_0722'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='link',
            field=models.CharField(max_length=400, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resource',
            name='type',
            field=models.IntegerField(default=1, max_length=2, choices=[(1, b'A lesson presentation'), (2, b'A lesson plan'), (3, b'A scheme of work'), (4, b'A link to a webpage'), (5, b'A link to a video')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='file',
            field=models.ForeignKey(blank=True, to='uploader.File', null=True),
            preserve_default=True,
        ),
    ]
