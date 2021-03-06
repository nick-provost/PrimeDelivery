# Generated by Django 2.2.24 on 2021-10-07 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0026_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='bio',
            field=models.CharField(max_length=250, null=True, verbose_name='Bio'),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='city',
            field=models.CharField(max_length=25, null=True, verbose_name='City'),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='postal_code',
            field=models.CharField(max_length=25, null=True, verbose_name='Postal Code'),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='shipping_address',
            field=models.CharField(max_length=60, null=True, verbose_name='Shipping Address'),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='state',
            field=models.CharField(max_length=25, null=True, verbose_name='State'),
        ),
    ]
