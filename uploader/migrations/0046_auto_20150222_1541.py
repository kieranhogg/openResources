# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0045_auto_20150222_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='read_date',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
