# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0010_auto_20150218_1524'),
    ]

    operations = [
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name=b'Title')),
                ('resource', models.ManyToManyField(to='uploader.Resource')),
            ],
            options={
                'ordering': ('title',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name=b'Title')),
                ('pub_date', models.DateTimeField(verbose_name=b'date published')),
                ('syllabus', models.ForeignKey(to='uploader.Syllabus')),
            ],
            options={
                'ordering': ('title',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnitTopic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name=b'Title')),
                ('pub_date', models.DateTimeField(verbose_name=b'date published')),
                ('topic', models.ForeignKey(to='uploader.Topic')),
                ('unit', models.ForeignKey(to='uploader.Unit')),
            ],
            options={
                'ordering': ('title',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='document',
            options={'ordering': ('docfile',)},
        ),
        migrations.AlterModelOptions(
            name='examboard',
            options={'ordering': ('board_name',)},
        ),
        migrations.AlterModelOptions(
            name='examlevel',
            options={'ordering': ('level_number', 'level_name')},
        ),
        migrations.AlterModelOptions(
            name='resource',
            options={'ordering': ('title',)},
        ),
        migrations.AlterModelOptions(
            name='subject',
            options={'ordering': ('subject_name',)},
        ),
        migrations.AlterModelOptions(
            name='syllabus',
            options={'ordering': ('exam_board', 'exam_level')},
        ),
        migrations.AlterField(
            model_name='resource',
            name='title',
            field=models.CharField(max_length=200, verbose_name=b'Title'),
            preserve_default=True,
        ),
    ]
