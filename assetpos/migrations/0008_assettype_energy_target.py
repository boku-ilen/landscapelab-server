# Generated by Django 2.2.1 on 2019-09-04 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assetpos', '0007_auto_20190904_1031'),
    ]

    operations = [
        migrations.AddField(
            model_name='assettype',
            name='energy_target',
            field=models.IntegerField(default=0),
        ),
    ]
