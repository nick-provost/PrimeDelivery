# Generated by Django 2.2.24 on 2021-10-20 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0032_auto_20211020_0842'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='points',
            field=models.IntegerField(default=0, verbose_name='Points'),
        ),
    ]
