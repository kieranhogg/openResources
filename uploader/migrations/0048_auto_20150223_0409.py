# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0047_auto_20150222_1543'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='file',
            options={'ordering': ('-pub_date',)},
        ),
        migrations.AlterModelOptions(
            name='licence',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ('-pub_date',)},
        ),
        migrations.AlterModelOptions(
            name='rating',
            options={'ordering': ('-pub_date',)},
        ),
        migrations.AlterModelOptions(
            name='resource',
            options={'ordering': ('-pub_date',)},
        ),
        migrations.AlterModelOptions(
            name='syllabus',
            options={'ordering': ('subject', 'exam_board', 'exam_level'), 'verbose_name_plural': 'Syllabuses'},
        ),
        migrations.RemoveField(
            model_name='resource',
            name='unittopic',
        ),
        migrations.AddField(
            model_name='resource',
            name='unit_topic',
            field=models.ForeignKey(blank=True, to='uploader.UnitTopic', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='examlevel',
            name='country',
            field=models.CharField(default=b'Any', help_text=b'This is free text, so please check spelling and caps', max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='file',
            name='filename',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='file',
            name='mimetype',
            field=models.CharField(max_length=200),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='message',
            name='type',
            field=models.IntegerField(max_length=1, choices=[(1, b'PrivateMessage'), (2, b'Announcement'), (3, b'Sticky')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='author',
            field=models.CharField(help_text=b'Who is the original author? E.g. John Smith. If you are the author, write "me"', max_length=200, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='author_link',
            field=models.CharField(help_text=b'A URL or email to credit the original author. If it is you, leave blank', max_length=200, null=True, blank=True),
            preserve_default=True,
        ),
    ]
