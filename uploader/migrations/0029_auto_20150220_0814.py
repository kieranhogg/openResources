# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0028_resource_subject'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='subject',
            field=models.ForeignKey(to='uploader.Subject'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='syllabus',
            field=smart_selects.db_fields.ChainedForeignKey(to='uploader.Syllabus'),
            preserve_default=True,
        ),
    ]
