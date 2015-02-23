# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0049_auto_20150223_0633'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='link',
            field=models.ForeignKey(blank=True, to='uploader.Bookmark', null=True),
            preserve_default=True,
        ),
    ]
