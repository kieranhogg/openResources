# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0036_auto_20150221_0748'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='description',
            field=models.TextField(help_text=b'E.g. the expected topics taught', null=True, blank=True),
            preserve_default=True,
        ),
    ]
