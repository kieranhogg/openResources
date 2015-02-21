# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0013_auto_20150219_0600'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='description',
            field=models.CharField(max_length=2000, null=True, verbose_name=b'Description'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='author',
            field=models.CharField(default=1, max_length=200, verbose_name=b'Title'),
            preserve_default=True,
        ),
    ]
