# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0027_remove_resource_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='subject',
            field=smart_selects.db_fields.ChainedForeignKey(default=1, to='uploader.Subject'),
            preserve_default=False,
        ),
    ]
