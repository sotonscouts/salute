from django.db import migrations


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL(
            """
            CREATE FUNCTION time_subtype_diff(x time, y time) RETURNS float8 AS
            'SELECT EXTRACT(EPOCH FROM (x - y))' LANGUAGE sql STRICT IMMUTABLE;

            CREATE TYPE timerange AS RANGE (
                subtype = time,
                subtype_diff = time_subtype_diff
            );
            """,
            """
            DROP TYPE IF EXISTS timerange;
            DROP FUNCTION IF EXISTS time_subtype_diff;
            """,
        ),
    ]
