# Generated by Django 4.0.5 on 2023-06-11 08:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_rename_name_subject_full_name_subject_short_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='arxivpaper',
            old_name='categories',
            new_name='subjects',
        ),
    ]
