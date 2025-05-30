# Generated by Django 4.2.17 on 2025-01-19 06:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('seller', '0003_seller_approval_notes'),
        ('catalogue', '0027_attributeoption_code_attributeoptiongroup_code_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='seller',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='seller.seller', verbose_name='Seller'),
        ),
    ]
