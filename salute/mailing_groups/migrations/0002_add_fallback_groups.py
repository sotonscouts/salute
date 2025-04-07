from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mailing_groups", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemmailinggroup",
            name="always_include_fallback_group",
            field=models.BooleanField(
                default=False,
                help_text="Whether to always include the fallback group in this group.",
            ),
        ),
        migrations.AddField(
            model_name="systemmailinggroup",
            name="fallback_group_composite_key",
            field=models.CharField(
                blank=True,
                help_text="The composite key of the fallback group to use if there are no members in this group.",
                max_length=255,
            ),
        ),
    ]
