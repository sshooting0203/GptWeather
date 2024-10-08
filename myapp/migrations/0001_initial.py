# Generated by Django 4.2.15 on 2024-08-13 00:09

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Weather',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.CharField(max_length=100, unique=True)),
                ('location', models.CharField(max_length=100)),
                ('data', models.JSONField()),
                ('recorded', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
