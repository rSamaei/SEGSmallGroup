# Generated by Django 5.1.2 on 2024-11-13 12:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tutorials', '0006_remove_requestsession_proficiency_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tutorsubject',
            old_name='proficiency_level',
            new_name='proficiency',
        ),
    ]
