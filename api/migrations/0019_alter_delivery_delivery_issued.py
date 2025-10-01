from datetime import datetime
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_delivery_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='transportation',
            name='date_requested',
            field=models.DateTimeField(
                auto_now_add=True,
                default=datetime(2025, 9, 22, 18, 30, 0)  # datetime object
            ),
            preserve_default=False,
        ),
    ]
