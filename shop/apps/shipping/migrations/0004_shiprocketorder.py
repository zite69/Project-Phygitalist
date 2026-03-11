from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shipping', '0003_auto_20181115_1953'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShipRocketOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(db_index=True, max_length=128, unique=True)),
                ('shiprocket_order_id', models.CharField(blank=True, max_length=64)),
                ('shipment_id', models.CharField(blank=True, max_length=64)),
                ('awb_code', models.CharField(blank=True, max_length=64)),
                ('courier_name', models.CharField(blank=True, max_length=128)),
                ('label_url', models.URLField(blank=True)),
                ('status', models.CharField(blank=True, max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('raw_response', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
