# Generated by Django 5.0 on 2024-01-07 11:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0002_rename_quantitiy_cartitem_quantity'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cartitem',
            options={'verbose_name': 'Cart Item', 'verbose_name_plural': 'Cart Items'},
        ),
    ]