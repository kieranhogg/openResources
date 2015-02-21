# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0009_resources'),
    ]

    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name=b'Exam Level')),
                ('pub_date', models.DateTimeField(verbose_name=b'date published')),
                ('syllabus', models.ForeignKey(to='uploader.Syllabus')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='resources',
            name='syllabus',
        ),
        migrations.DeleteModel(
            name='Resources',
        ),
    ]
