# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0042_syllabus_subject_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='filesize',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='resource',
            name='author_link',
            field=models.CharField(help_text=b'A URL or email to credit the original author. If it is you, leave blank', max_length=200, null=True, verbose_name=b'Author Link', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='topics',
            field=models.ManyToManyField(to='uploader.Topic', null=True, blank=True),
            preserve_default=True,
        ),
    ]
