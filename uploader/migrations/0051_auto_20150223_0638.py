# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0050_resource_link'),
    ]

    operations = [
        migrations.RenameField(
            model_name='resource',
            old_name='link',
            new_name='bookmark',
        ),
    ]
