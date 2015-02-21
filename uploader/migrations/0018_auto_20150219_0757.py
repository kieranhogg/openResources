# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0017_auto_20150219_0650'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='author_link',
            field=models.CharField(help_text=b'A URL or email to credit the original author. If it is you, leave blank', max_length=200, null=True, verbose_name=b'Author Link'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='licence',
            name='link',
            field=models.CharField(max_length=200, verbose_name=b'URL'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='author',
            field=models.CharField(default=1, help_text=b'Who is the original author? E.g. John Smith. If you are the author, write "me"', max_length=200, verbose_name=b'Author'),
            preserve_default=True,
        ),
    ]
