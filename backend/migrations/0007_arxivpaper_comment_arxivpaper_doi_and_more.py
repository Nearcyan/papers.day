# Generated by Django 4.0.5 on 2023-06-11 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0006_arxivpaper_primary_subject_alter_arxivpaper_subjects'),
    ]

    operations = [
        migrations.AddField(
            model_name='arxivpaper',
            name='comment',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='arxivpaper',
            name='doi',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='arxivpaper',
            name='journal_ref',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]