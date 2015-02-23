# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0043_auto_20150222_1536'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='read_date',
            field=models.DateTimeField(),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='message',
            name='sticky_date',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
    ]
