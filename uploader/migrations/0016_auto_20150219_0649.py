# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0015_auto_20150219_0612'),
    ]

    operations = [
        migrations.CreateModel(
            name='Licence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name=b'Title')),
                ('description', models.TextField(null=True, verbose_name=b'Description')),
                ('link', models.CharField(max_length=200, verbose_name=b'Title')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='resource',
            name='licence',
            field=models.ForeignKey(null=True, to='uploader.Licence'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='author',
            field=models.CharField(default=1, max_length=200, verbose_name=b'Author'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='resource',
            name='file',
            field=models.FileField(null=True, upload_to=b''),
            preserve_default=True,
        ),
    ]
