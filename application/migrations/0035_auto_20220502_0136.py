# Generated by Django 3.2.8 on 2022-05-02 01:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0034_auto_20220406_0128'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='media',
            options={'ordering': ('id',)},
        ),
        migrations.AlterField(
            model_name='media',
            name='file',
            field=models.FileField(upload_to='videos/'),
        ),
    ]