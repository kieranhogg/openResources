# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import smart_selects.db_fields


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0025_unittopic_topic'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='subject',
            field=smart_selects.db_fields.ChainedForeignKey(default=1, to='uploader.Subject'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='resource',
            name='licence',
            field=models.ForeignKey(to='uploader.Licence', help_text=b'It is important to only share resources that are either yours, or are already under a licence which allows you to share them', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='unittopic',
            field=models.ForeignKey(verbose_name=b'Unit Topic', blank=True, to='uploader.UnitTopic', null=True),
            preserve_default=True,
        ),
    ]
