from django.db import migrations, models
from django.utils import timezone

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_alter_delivery_delivery_issued'),
    ]

    operations = [
        migrations.AlterField(
            model_name='delivery',
            name='delivery_issued',
            field=models.DateTimeField(
                auto_now_add=True,
                default=timezone.now
            ),
            preserve_default=False,
        ),
    ]
