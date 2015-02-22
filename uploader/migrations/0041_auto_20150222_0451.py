# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uploader', '0040_auto_20150221_1541'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.TextField()),
                ('type', models.IntegerField(max_length=1, choices=[(1, b'Private Message'), (2, b'Announcement sent to all users'), (3, b'A message which is stuck to all pages until a certain date')])),
                ('read', models.BooleanField(default=False)),
                ('read_date', models.DateTimeField(auto_now_add=True)),
                ('sticky_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('pub_date', models.DateTimeField(auto_now_add=True)),
                ('user_from', models.ForeignKey(related_name='message_user_from', to=settings.AUTH_USER_MODEL)),
                ('user_to', models.ForeignKey(related_name='message_user_to', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('pub_date',),
            },
            bases=(models.Model,),
        ),
        migrations.DeleteModel(
            name='Document',
        ),
        migrations.AlterModelOptions(
            name='rating',
            options={'ordering': ('pub_date',)},
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'ordering': ('user',)},
        ),
        migrations.AlterField(
            model_name='examboard',
            name='pub_date',
            field=models.DateTimeField(verbose_name=b'Date published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='examlevel',
            name='pub_date',
            field=models.DateTimeField(verbose_name=b'Date published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='file',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Date published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='licence',
            name='description',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='licence',
            name='name',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'Date published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='title',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='subject',
            name='pub_date',
            field=models.DateTimeField(verbose_name=b'Date published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='syllabus',
            name='pub_date',
            field=models.DateTimeField(verbose_name=b'Date published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='topic',
            name='title',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='unit',
            name='pub_date',
            field=models.DateTimeField(verbose_name=b'Date published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='unit',
            name='title',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='unittopic',
            name='pub_date',
            field=models.DateTimeField(verbose_name=b'Date published'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='unittopic',
            name='title',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
    ]
