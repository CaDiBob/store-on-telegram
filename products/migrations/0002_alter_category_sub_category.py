# Generated by Django 4.0 on 2023-02-26 07:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='sub_category',
            field=models.ManyToManyField(to='products.Category', verbose_name='Подкатегория'),
        ),
    ]
