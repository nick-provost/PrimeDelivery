# Generated by Django 2.2.24 on 2021-10-21 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0033_application_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='awardpoints',
            name='reason',
            field=models.CharField(default='N/A', max_length=250, verbose_name='Reason'),
        ),
    ]
