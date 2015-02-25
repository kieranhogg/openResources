# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0054_auto_20150224_1723'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='author',
            field=models.CharField(help_text=b'Who is the original author? E.g. John Smith. If you are the author, write "me" if you are logged in, otherwise add your name', max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='file',
            name='author_link',
            field=models.CharField(help_text=b"A URL or email to credit the original author. If it is you and you're logged in, leave blank", max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
    ]
