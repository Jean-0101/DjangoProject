# Generated by Django 5.1.3 on 2024-11-30 10:55

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_customuser_remaining_leave_hours_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailylog',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
