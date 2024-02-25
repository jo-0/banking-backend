# Generated by Django 4.1.3 on 2022-11-09 05:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("balance", models.IntegerField()),
                ("bank_name", models.CharField(max_length=24)),
                ("branch", models.CharField(max_length=12)),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "accounts",
            },
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateTimeField(auto_now_add=True)),
                ("amount", models.PositiveIntegerField()),
                ("note", models.CharField(max_length=48)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Success", "Success"),
                            ("Failed", "Failed"),
                            ("Pending", "Pending"),
                        ],
                        max_length=8,
                        null=True,
                    ),
                ),
                (
                    "transaction_type",
                    models.CharField(
                        choices=[("Debit", "Withdraw"), ("Credit", "Deposit")],
                        max_length=12,
                    ),
                ),
                (
                    "from_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="from_account",
                        to="savings_bank.account",
                    ),
                ),
                (
                    "to_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="to_account",
                        to="savings_bank.account",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "transactions",
            },
        ),
    ]
