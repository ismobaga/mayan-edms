# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-26 19:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('converter', '0014_auto_20190626_1904'),
    ]

    operations = [
        migrations.CreateModel(
            name='Redaction',
            fields=[
            ],
            options={
                'verbose_name': 'Redaction',
                'proxy': True,
                'verbose_name_plural': 'Redactions',
                'indexes': [],
            },
            bases=('converter.transformation',),
        ),
    ]
