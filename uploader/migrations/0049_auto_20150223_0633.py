# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uploader', '0048_auto_20150223_0409'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('link', models.CharField(max_length=400)),
                ('description', models.TextField(null=True, verbose_name=b'Description')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name=b'Date published')),
                ('uploader', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-pub_date',),
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='resource',
            name='author',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='author_link',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='description',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='licence',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='link',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='title',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='topics',
        ),
        migrations.RemoveField(
            model_name='resource',
            name='type',
        ),
        migrations.AddField(
            model_name='file',
            name='author',
            field=models.CharField(help_text=b'Who is the original author? E.g. John Smith. If you are the author, write "me"', max_length=200, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='author_link',
            field=models.CharField(help_text=b'A URL or email to credit the original author. If it is you, leave blank', max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='description',
            field=models.TextField(null=True, verbose_name=b'Description'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='licence',
            field=models.ForeignKey(to='uploader.Licence', help_text=b'<a href="uploader/licences/">Help with the licences</a>', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='title',
            field=models.CharField(default='default title', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='file',
            name='topics',
            field=models.ManyToManyField(to='uploader.Topic', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='type',
            field=models.IntegerField(default=1, max_length=2, choices=[(1, b'A lesson presentation'), (2, b'A lesson plan'), (3, b'A scheme of work')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='file',
            name='uploader',
            field=models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
