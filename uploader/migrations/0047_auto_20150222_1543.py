# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0046_auto_20150222_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='user_to',
            field=models.ForeignKey(related_name='message_user_to', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
