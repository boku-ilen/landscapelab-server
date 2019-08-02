# Generated by Django 2.0.3 on 2019-07-28 20:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='default_wind_direction',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='scenario',
            name='energy_requirement_summer',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='scenario',
            name='energy_requirement_total',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='scenario',
            name='energy_requirement_winter',
            field=models.FloatField(default=0),
        ),
    ]
