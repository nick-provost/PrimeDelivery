# Generated by Django 2.2.24 on 2021-10-07 19:36

import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0028_auto_20211007_1158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useraccount',
            name='profile_pic',
            field=models.ImageField(blank=True, default='/static/profile_pics/AD.png', null=True, upload_to=accounts.models.UserAccount.upload_path),
        ),
    ]
