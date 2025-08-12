### Overview

We store annual data from the national Scouting Census for sections and provide derived metrics for reporting.

Data is imported from JSON files (one per section/year) and persisted as `SectionCensusReturn` records with database-generated fields for efficient querying.

### Data model

- `SectionCensusReturn`
  - **section**: FK to `hierarchy.Section`
  - **year**: Positive integer (e.g. 2020)
  - **data_format_version**: Small integer, defaults to V1
  - **data**: JSON payload from the census export
  - Computed fields (database-generated):
    - **annual_subs_cost**: Decimal(6, 2). Extracted from `data["annual_cost"]` and cast to decimal
    - **total_volunteers**: Integer. Sum of volunteer counts by regex
    - **total_young_people**: Integer. Sum of young people counts by regex
    - **ratio_young_people_to_volunteers**: Decimal(6, 2). Rounded to 2dp

Ordering defaults to newest first (`-year`) and there is an index on `year` for filtering.

### Expected JSON structure for import (V1)

Each file represents one section/year. Minimal required keys:

- `reg_no`: Section shortcode (matches `Section.shortcode`)
- `year`: Year as string or integer (e.g. "2020")
- `data`: Object containing numeric string values for counts and other fields
- Optional `file`: Original source filename (not used for import logic)

Example:

```json
{
  "file": "447607-2020.html",
  "reg_no": "S10042555",
  "year": "2020",
  "data": {
    "annual_cost": "100",
    "y_4_m": "7",
    "y_4_f": "6",
    "y_4_p": "1",
    "y_4_s": "0",
    "l_asl_m": "5",
    "l_sl_f": "4",
    "l_asl_p": "2",
    "l_sl_s": "1"
  }
}
```

Notes:
- The importer requires `data`, `reg_no`, and `year`.
- `data` must be a JSON object. Non-object types will be rejected.

### Importing data

Use the management command to import a directory of JSON files:

```bash
poetry run ./manage.py import_census_returns /path/to/json_dir \
  --dry-run            # optional: report actions only
  --fail-fast          # optional: stop on first error
  --format-version 1   # optional: defaults to 1
```

Behaviour:
- Files are processed in sorted order (glob `*.json`).
- Upserts by `(section, year)` using `update_or_create`.
- `--dry-run` prints CREATE/UPDATE without writing.
- `--fail-fast` raises on first error; otherwise logs and continues.

### Computed fields and regexes

Two PostgreSQL functions are installed via migration:
- `j_sum_by_regex_key(j jsonb, regex text) -> int`
  - Sums values of keys matching `regex` at the top level of `j`.
  - Only numeric string values are included (`^[0-9]+$`); others are ignored.
- `ratio(n int, d int) -> numeric`
  - Returns `ROUND(n / NULLIF(d, 0), 2)`; yields `0` when `d` is `0`.

Derived field definitions:
- **total_young_people**: `^y_[0-9]+_(m|f|p|s)$`
- **total_volunteers**: `^l_[a-z]+_(m|f|p|s|xm|xf|xp|xs)$`
- **annual_subs_cost**: `data["annual_cost"]` cast to decimal
- **ratio_young_people_to_volunteers**: `ratio(total_young_people, total_volunteers)`

### Error handling and validation

- Missing required keys (`data`, `reg_no`, `year`) cause a failure for that file.
- `data` must be a dictionary; otherwise the file is rejected.
- If `reg_no` does not match a unique `Section.shortcode`, the file is rejected.
- Non-numeric values for matching `y_*` or `l_*` keys are ignored in sums (they do not break the import).

### Database requirements

- PostgreSQL is required for the custom SQL functions and generated columns used by this feature.
- Running migrations installs the functions and generated fields.

### Notes on JSON source

The JSON files are produced by a separate process that extracts census information. They must adhere to the structure described above. If additional keys or formats are introduced in the future, bump `data_format_version` and extend the model/regexes accordingly.

If you have a repository or script that generates these files, document its output schema to ensure compatibility (e.g. how volunteer and young people counts are keyed, and where subscription cost is stored).

### JSON source and generation (reference)

Locally, JSON files can be generated using the separate `census-processing` workspace:
- Scripts:
  - `scrape_returns.py`: fetches raw census HTML/inputs
  - `parse_data.py`: parses and normalises into JSON files under `data/processed-returns/`
- Output naming: `data/processed-returns/{reg_no}-{year}.json`
- Each output contains the top-level keys: `data`, `file`, `reg_no`, `year` (confirmed via samples)

To import those locally generated files into Salute:

```bash
poetry run ./manage.py import_census_returns /Users/dan/Code/scouts/census-investigation/data/processed-returns --dry-run
```

This will validate structure and report which records would be created/updated. Remove `--dry-run` to persist changes.

### How HTML is processed into JSON

The JSON files are generated from the official census website’s HTML using a two-step process in the `census-investigation` workspace.

1) Scraping approved returns
- Script: `scrape_returns.py`
- Logs in using `CENSUS_USERNAME` and `CENSUS_PASSWORD`.
- Discovers section "census IDs" from group index pages.
- Fetches the detailed section page for each year and only saves those with status `Approved` to `data/returns/{sectionId}-{year}.html`.

2) Parsing HTML into normalised JSON
- Script: `parse_data.py`
- Extracts `year` and `reg_no` (section shortcode) from the HTML header using a regex like `(20\d{2}) - Reg no: (S\d+)`.
- Scans the page for elements with both `data-key` and `data-value` attributes.
- Filters out unwanted keys:
  - By prefix: `school_*`, `approve_for_*`, `approve*`, `contact*`
  - By name: `meetingplace`, `records`, `records_other`, `section_type`, `dow`
- Validates there are no duplicate keys.
- Writes `data/processed-returns/{reg_no}-{year}.json` with shape:
  - `file`: original HTML filename
  - `year`: e.g. `"2023"`
  - `reg_no`: e.g. `"S10012345"`
  - `data`: dict of key/value pairs (all values are strings in the source)

This is the directory you pass to the Salute import command.

### Key naming and semantics

Counts for young people and volunteers follow a compact naming convention in the `data` object. Values are numeric strings:

- Young people keys: `y_{age}_{suffix}`
  - `age`: numeric age, e.g. `4`, `5`, `6`, …
  - `suffix`: one of `m`, `f`, `p`, `s`
    - `m`: male
    - `f`: female
    - `p`: prefer not to say / prefer to self-describe
    - `s`: self-described / not specified
  - Examples: `y_4_m`, `y_5_f`, `y_7_p`, `y_6_s`

- Volunteer keys: `l_{role}_{suffix}`
  - `role`: a short role identifier made of lowercase letters, e.g. `asl`, `sl`, `dg`, `yl`, `sa`
  - `suffix` for volunteers includes extended forms for “prefer not to say/self-described”:
    - Basic: `m`, `f`, `p`, `s`
    - Recorded elsewhere too: `xm`, `xf`, `xp`, `xs`
  - Examples: `l_sl_m`, `l_asl_f`, `l_dg_p`, `l_yl_xf`

Salute computes derived fields from these keys using database functions:
- `total_young_people` sums keys matching regex: `^y_[0-9]+_(m|f|p|s)$`
- `total_volunteers` sums keys matching regex: `^l_[a-z]+_(m|f|p|s|xm|xf|xp|xs)$`
- Non-numeric values among matching keys are ignored for sums.

Other notable keys:
- `annual_cost`: subscription amount for the year (string). Stored as decimal in Salute’s `annual_subs_cost` generated column.
- Additional keys may exist for disabilities (`dis_*`), relationships (`rel_*`), etc., which are currently stored raw under `data` and not aggregated.

If the naming scheme changes in future exports, adjust the regexes or bump `data_format_version` to encode the new shape.
