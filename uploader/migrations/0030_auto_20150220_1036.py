# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0029_auto_20150220_0814'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=200, verbose_name=b'Filename')),
                ('file', models.FileField(upload_to=b'')),
                ('mimetype', models.CharField(max_length=200, verbose_name=b'Mimetype')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name=b'date published')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='resource',
            name='syllabus',
            field=models.ForeignKey(to='uploader.Syllabus'),
            preserve_default=True,
        ),
    ]
