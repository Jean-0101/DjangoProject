# Generated by Django 5.1.3 on 2024-11-29 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_alter_dailylog_check_in_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailylog',
            name='check_in_time',
            field=models.DateTimeField(),
        ),
    ]
