# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0031_remove_resource_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='file',
            field=models.ForeignKey(default=1, to='uploader.File'),
            preserve_default=False,
        ),
    ]
