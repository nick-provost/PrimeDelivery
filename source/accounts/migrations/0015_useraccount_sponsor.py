# Generated by Django 2.2.24 on 2021-09-23 21:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_useraccount_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='sponsor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.SponsorOrganization'),
        ),
    ]
