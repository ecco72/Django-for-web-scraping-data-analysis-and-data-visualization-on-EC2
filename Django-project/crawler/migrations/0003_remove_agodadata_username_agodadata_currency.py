# Generated by Django 4.2.13 on 2024-06-27 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crawler', '0002_alter_agodadata_options_agodadata_username'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='agodadata',
            name='username',
        ),
        migrations.AddField(
            model_name='agodadata',
            name='currency',
            field=models.CharField(default='TWD', max_length=50),
        ),
    ]
