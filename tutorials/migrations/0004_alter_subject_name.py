# Generated by Django 5.1.2 on 2024-11-13 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorials', '0003_user_user_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(max_length=20),
        ),
    ]
