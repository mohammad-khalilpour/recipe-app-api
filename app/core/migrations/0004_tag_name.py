# Generated by Django 3.2.20 on 2023-07-29 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20230729_0811'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='name',
            field=models.CharField(default='tags', max_length=255),
            preserve_default=False,
        ),
    ]
