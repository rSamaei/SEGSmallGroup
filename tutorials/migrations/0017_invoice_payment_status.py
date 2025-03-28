# Generated by Django 5.1.2 on 2024-12-02 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorials', '0016_tutorsubject_price_alter_requestsession_frequency_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='payment_status',
            field=models.CharField(choices=[('paid', 'Paid'), ('waiting', 'Waiting for confirmation'), ('unpaid', 'Unpaid')], default='unpaid', max_length=10),
        ),
    ]
