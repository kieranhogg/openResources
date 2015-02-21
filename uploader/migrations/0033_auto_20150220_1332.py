# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0032_resource_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='licence',
            field=models.ForeignKey(to='uploader.Licence', help_text=b'<a href="uploader/licences/">Help with the licences</a>', null=True),
            preserve_default=True,
        ),
    ]
