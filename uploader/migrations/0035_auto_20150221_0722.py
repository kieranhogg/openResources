# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0034_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rating',
            name='rating',
            field=models.IntegerField(max_length=1, choices=[(0, b'Just awful'), (1, b'Very poor'), (2, b'Poor'), (3, b'Mediocre'), (4, b'Good'), (5, b'Very good')]),
            preserve_default=True,
        ),
    ]
