# Generated by Django 5.1.2 on 2024-12-04 19:26


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorials', '0018_match_tutor_approved'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestsession',
            name='frequency',
            field=models.DecimalField(choices=[(0.25, 'Monthly'), (0.5, 'Fortnightly'), (1, 'Weekly'), (2, 'Biweekly')], decimal_places=2, default=1.0, max_digits=3),
        ),
    ]
