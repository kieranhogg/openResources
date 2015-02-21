# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0018_auto_20150219_0757'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='approved',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='author',
            field=models.CharField(help_text=b'Who is the original author? E.g. John Smith. If you are the author, write "me"', max_length=200, null=True, verbose_name=b'Author'),
            preserve_default=True,
        ),
    ]
