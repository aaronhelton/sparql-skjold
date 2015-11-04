# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('thesaurus', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cache',
            name='result_set',
            field=jsonfield.fields.JSONField(),
        ),
    ]
