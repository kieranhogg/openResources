# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='examlevel',
            name='level_number',
            field=models.CharField(default=b'0', max_length=1, choices=[(b'0', b'None'), (b'3', b'KS3'), (b'4', b'KS4'), (b'5', b'KS5')]),
            preserve_default=True,
        ),
    ]
