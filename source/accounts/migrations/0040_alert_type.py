# Generated by Django 2.2.24 on 2021-10-24 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0039_auto_20211024_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='alert',
            name='type',
            field=models.CharField(max_length=15, null=True, verbose_name='Alert Type'),
        ),
    ]
