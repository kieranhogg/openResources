# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uploader', '0012_auto_20150219_0534'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='file',
            field=models.FileField(default='blah', upload_to=b''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resource',
            name='uploader',
            field=models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
