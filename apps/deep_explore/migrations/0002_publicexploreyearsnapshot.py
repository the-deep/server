# Generated by Django 3.2.15 on 2023-01-22 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deep_explore', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicExploreYearSnapshot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.SmallIntegerField(unique=True)),
                ('file', models.FileField(max_length=255, upload_to='deep-explore/public-snapshot/')),
            ],
        ),
    ]
