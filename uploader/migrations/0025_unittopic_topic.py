# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0024_remove_unittopic_topic'),
    ]

    operations = [
        migrations.AddField(
            model_name='unittopic',
            name='topic',
            field=models.ManyToManyField(to='uploader.Topic'),
            preserve_default=True,
        ),
    ]
