# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uploader', '0033_auto_20150220_1332'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rating', models.IntegerField(max_length=1, choices=[(b'0', b'Just terrible'), (b'1', b'Still pretty terrible'), (b'2', b'Mediocre'), (b'3', b'Good'), (b'4', b'Very Good'), (b'5', b'Excellent')])),
                ('pub_date', models.DateTimeField(auto_now_add=True)),
                ('resource', models.ForeignKey(to='uploader.Resource')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
