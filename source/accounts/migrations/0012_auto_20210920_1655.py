# Generated by Django 2.2.24 on 2021-09-20 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_activation_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activation',
            name='email',
            field=models.EmailField(blank=True, max_length=25),
        ),
    ]