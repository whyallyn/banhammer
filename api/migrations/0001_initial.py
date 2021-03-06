# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-27 09:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Target',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_action', models.CharField(choices=[('ban', 'Ban'), ('allow', 'Allow')], max_length=5)),
                ('target_type', models.CharField(choices=[('ip', 'IP Address'), ('domain', 'Domain'), ('url', 'URL'), ('hash', 'Hash'), ('user', 'User')], max_length=6)),
                ('target', models.CharField(max_length=900)),
                ('reason', models.CharField(max_length=50)),
                ('method', models.CharField(max_length=50)),
                ('user', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'permissions': (('target_all_read', 'Read access for all Target types'), ('target_all_write', 'Write access for all Target types'), ('target_ipaddr_read', 'Read access for IP Target types'), ('target_ipaddr_write', 'Write access for IP Target types'), ('target_domain_read', 'Read access for Domain Target types'), ('target_domain_write', 'Write access for Domain Target types'), ('target_url_read', 'Read access for URL Target types'), ('target_url_write', 'Write access for URL Target types'), ('target_hash_read', 'Read access for Hash Target types'), ('target_hash_write', 'Write access for Hash Target types'), ('target_user_read', 'Read access for User Target types'), ('target_user_write', 'Write access for User Target types')),
            },
        ),
        migrations.CreateModel(
            name='TargetIpAddr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ipaddr', models.CharField(max_length=45, unique=True)),
                ('ipaddr_action', models.CharField(choices=[('ban', 'Ban'), ('allow', 'Allow')], max_length=5)),
                ('method', models.CharField(max_length=50)),
                ('target', models.ManyToManyField(to='api.Target')),
            ],
        ),
    ]
