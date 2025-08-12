import json
from pathlib import Path
from typing import Any

from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from salute.hierarchy.models import Section
from salute.stats.models import SectionCensusDataFormatVersion, SectionCensusReturn


class Command(BaseCommand):
    help = """Import section census returns from a directory of JSON files.

Expected JSON structure per file:
{
  "data": { ... },
  "file": "447607-2020.html",
  "reg_no": "S10042555",
  "year": "2020"
}"""

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "directory",
            type=str,
            help="Path to a directory containing JSON files to import",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse files and report actions without writing to the database",
        )
        parser.add_argument(
            "--fail-fast",
            action="store_true",
            help="Stop at the first error instead of continuing",
        )
        parser.add_argument(
            "--format-version",
            type=int,
            choices=[SectionCensusDataFormatVersion.V1],
            default=SectionCensusDataFormatVersion.V1,
            help="Data format version for imported records (default: v1)",
        )

    def handle(self, *args: str, **options: Any) -> None:
        directory = Path(str(options["directory"]))
        dry_run = bool(options["dry_run"])
        fail_fast = bool(options["fail_fast"])
        data_format_version = int(options["format_version"])

        if not directory.exists() or not directory.is_dir():
            raise CommandError(f"Directory not found: {directory}")

        pattern = "*.json"
        files = sorted(directory.glob(pattern))
        if not files:
            self.stdout.write(self.style.WARNING("No JSON files found to import."))
            return

        created_count = 0
        updated_count = 0
        error_count = 0

        self.stdout.write(f"Scanning {len(files)} file(s) in {directory} (dry_run={dry_run})")

        for file_path in files:
            try:
                with file_path.open("r", encoding="utf-8") as fh:
                    payload = json.load(fh)

                # Basic validation
                for key in ("data", "reg_no", "year"):
                    if key not in payload:
                        raise ValueError(f"Missing required key '{key}' in {file_path}")

                reg_no = str(payload["reg_no"]).strip()
                try:
                    year = int(payload["year"])
                except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
                    raise ValueError(f"Invalid 'year' value in {file_path}: {payload['year']}") from exc

                data = payload["data"]
                if not isinstance(data, dict):
                    raise ValueError(f"Invalid 'data' value in {file_path}: expected object, got {type(data).__name__}")

                try:
                    section = Section.objects.get(shortcode=reg_no)
                except Section.DoesNotExist:
                    raise CommandError(
                        f"No section found with shortcode/reg_no '{reg_no}' (file: {file_path.name})"
                    ) from None
                except MultipleObjectsReturned:  # pragma: no cover - should not happen if shortcode is unique
                    raise CommandError(
                        f"Multiple sections found with shortcode/reg_no '{reg_no}' (file: {file_path.name})"
                    ) from None

                if dry_run:
                    exists = SectionCensusReturn.objects.filter(section=section, year=year).exists()
                    if exists:
                        action = "UPDATE"
                        updated_count += 1
                    else:
                        action = "CREATE"
                        created_count += 1
                    self.stdout.write(f"{action} section={section.id} year={year} from {file_path.name}")
                    continue

                with transaction.atomic():
                    _, created = SectionCensusReturn.objects.update_or_create(
                        section=section,
                        year=year,
                        defaults={
                            "data_format_version": data_format_version,
                            "data": data,
                        },
                    )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created census return for {section} ({year})"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated census return for {section} ({year})"))

            except Exception as exc:  # noqa: BLE001
                error_count += 1
                msg = f"Error processing {file_path}: {exc}"
                if fail_fast:
                    raise CommandError(msg) from exc
                self.stderr.write(self.style.ERROR(msg))
                continue

        self.stdout.write(f"Finished: created={created_count}, updated={updated_count}, errors={error_count}")
