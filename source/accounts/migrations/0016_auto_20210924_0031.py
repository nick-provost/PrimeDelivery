# Generated by Django 2.2.24 on 2021-09-24 00:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_useraccount_sponsor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useraccount',
            name='avatar',
        ),
        migrations.AddField(
            model_name='useraccount',
            name='profile_pic',
            field=models.ImageField(blank=True, default='AD.png', null=True, upload_to=''),
        ),
    ]
