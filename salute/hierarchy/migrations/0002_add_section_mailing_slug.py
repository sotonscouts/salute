from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("hierarchy", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="section",
            name="mailing_slug",
            field=models.CharField(
                blank=True,
                help_text="Slug for generating mailing lists. Do not change unless you understand the impact. Only applicable to district sections.",  # noqa: E501
                max_length=64,
            ),
        ),
        migrations.AddConstraint(
            model_name="section",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("section_type__in", ["Explorers", "Young Leader", "Network"]),
                    ("mailing_slug", ""),
                    _connector="OR",
                ),
                name="only_district_sections_can_have_mailing_slug",
                violation_error_message="Only district sections can have a mailing slug",
            ),
        ),
    ]
