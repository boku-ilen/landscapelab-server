# Generated by Django 2.1.5 on 2019-03-13 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0002_auto_20190304_2207'),
    ]

    operations = [
        migrations.AddField(
            model_name='speciesrepresentation',
            name='distribution_density',
            field=models.FloatField(default=1),
        ),
    ]