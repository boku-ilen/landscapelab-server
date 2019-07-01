# Generated by Django 2.1.5 on 2019-07-01 19:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vegetation', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='phytocoenosis',
            name='distribution_graphic_path',
        ),
        migrations.RemoveField(
            model_name='phytocoenosis',
            name='max_height',
        ),
        migrations.RemoveField(
            model_name='phytocoenosis',
            name='max_slope',
        ),
        migrations.RemoveField(
            model_name='phytocoenosis',
            name='min_height',
        ),
        migrations.RemoveField(
            model_name='phytocoenosis',
            name='min_slope',
        ),
        migrations.AlterField(
            model_name='speciesrepresentation',
            name='avg_height',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='speciesrepresentation',
            name='species',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='vegetation.Species'),
        ),
    ]
