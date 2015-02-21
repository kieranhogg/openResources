# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0004_auto_20150218_0553'),
    ]

    operations = [
        migrations.AddField(
            model_name='exam',
            name='pub_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 18, 6, 3, 21, 821613, tzinfo=utc), verbose_name=b'date published'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='examboard',
            name='pub_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 18, 6, 3, 31, 825308, tzinfo=utc), verbose_name=b'date published'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='examlevel',
            name='pub_date',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 18, 6, 3, 38, 707276, tzinfo=utc), verbose_name=b'date published'),
            preserve_default=False,
        ),
    ]
