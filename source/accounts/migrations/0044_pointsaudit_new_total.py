# Generated by Django 2.2.24 on 2021-11-16 16:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0043_passwordchangeaudit'),
    ]

    operations = [
        migrations.AddField(
            model_name='pointsaudit',
            name='new_total',
            field=models.IntegerField(default=0, verbose_name='New Total'),
        ),
    ]
