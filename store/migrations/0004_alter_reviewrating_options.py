# Generated by Django 5.0 on 2024-02-18 10:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_reviewrating'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='reviewrating',
            options={'verbose_name': 'Review Rating', 'verbose_name_plural': 'Review Ratings'},
        ),
    ]
