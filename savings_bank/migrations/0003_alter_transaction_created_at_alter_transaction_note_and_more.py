# Generated by Django 4.1.3 on 2022-11-09 14:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("savings_bank", "0002_rename_date_transaction_created_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="date"),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="note",
            field=models.CharField(max_length=48, null=True),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="status",
            field=models.CharField(
                choices=[
                    ("Success", "Success"),
                    ("Failed", "Failed"),
                    ("Pending", "Pending"),
                ],
                default="Pending",
                max_length=8,
            ),
        ),
    ]
