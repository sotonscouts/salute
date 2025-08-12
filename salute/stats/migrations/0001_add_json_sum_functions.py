from django.db import migrations

SQL_CREATE_J_SUM_BY_REGEX_KEY = """
    CREATE OR REPLACE FUNCTION j_sum_by_regex_key(j jsonb, regex text)
    RETURNS int
    LANGUAGE sql IMMUTABLE AS $$
      SELECT COALESCE(SUM((v)::int), 0)
      FROM jsonb_each_text(j) AS e(k, v)
      WHERE k ~ regex
        AND v ~ '^[0-9]+$'
    $$;
    """

SQL_DROP_J_SUM_BY_REGEX_KEY = "DROP FUNCTION IF EXISTS j_sum_by_regex_key(jsonb, text);"

# Compute a ratio n/d as a numeric rounded to 2 decimal places.
# If d is zero (or NULL), return 0 to avoid division errors.
SQL_CREATE_RATIO = """
    CREATE OR REPLACE FUNCTION ratio(n integer, d integer)
    RETURNS numeric
    LANGUAGE sql IMMUTABLE AS $$
      SELECT COALESCE(ROUND(n::numeric / NULLIF(d, 0), 2), 0)
    $$;
    """

SQL_DROP_RATIO = "DROP FUNCTION IF EXISTS ratio(integer, integer);"


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=SQL_CREATE_J_SUM_BY_REGEX_KEY,
            reverse_sql=SQL_DROP_J_SUM_BY_REGEX_KEY,
        ),
        migrations.RunSQL(
            sql=SQL_CREATE_RATIO,
            reverse_sql=SQL_DROP_RATIO,
        ),
    ]
