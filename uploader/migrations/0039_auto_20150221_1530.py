# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0038_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='unittopic',
            name='description',
            field=models.TextField(help_text=b'E.g. the expected topics taught', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='unit',
            name='description',
            field=models.TextField(help_text=b'A brief overview of the content', null=True, blank=True),
            preserve_default=True,
        ),
    ]
