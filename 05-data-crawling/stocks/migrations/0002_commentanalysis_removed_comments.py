from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('stocks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentanalysis',
            name='removed_comments',
            field=models.JSONField(default=list),
        ),
    ]
