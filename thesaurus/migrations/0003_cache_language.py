# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thesaurus', '0002_auto_20151104_1824'),
    ]

    operations = [
        migrations.AddField(
            model_name='cache',
            name='language',
            field=models.CharField(default='en', max_length=2),
            preserve_default=False,
        ),
    ]
