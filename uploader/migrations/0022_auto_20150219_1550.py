# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0021_examlevel_country'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topic',
            name='resource',
        ),
        migrations.AddField(
            model_name='resource',
            name='topics',
            field=models.ManyToManyField(to='uploader.Topic'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resource',
            name='unit',
            field=models.ForeignKey(blank=True, to='uploader.Unit', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resource',
            name='unittopic',
            field=models.ForeignKey(blank=True, to='uploader.UnitTopic', null=True),
            preserve_default=True,
        ),
    ]
