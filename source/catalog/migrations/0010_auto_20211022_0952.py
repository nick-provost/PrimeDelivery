# Generated by Django 2.2.24 on 2021-10-22 14:52

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0009_auto_20211020_1752'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogitem',
            name='last_updated',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True, verbose_name='DateTime of the Last Update to Item'),
        ),
    ]
