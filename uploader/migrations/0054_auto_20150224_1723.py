# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0053_auto_20150224_1025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='licence',
            field=models.ForeignKey(to='uploader.Licence', help_text=b'<br />When submitting your work, you need to choose how you want people to use it. If submitting others\', you must respect any existing licences. (<strong>Attribution-NonCommercial-ShareAlike</strong> is a safe bet for new resources) <a href="/licences/">Still unsure?</a> ', null=True),
            preserve_default=True,
        ),
    ]
