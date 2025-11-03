"""Compare headers between corresponding CSV or TXT files in two directories.

The script inspects the contents of two directories, pairs files that share the
same filename (case-sensitive), and compares the first row of each file as a
CSV header.  A summary CSV is generated describing which files match and which
ones differ, including the specific header names that are missing from either
file.

Usage
-----

```
python compare_headers.py DIR1 DIR2 [-o OUTPUT]
```

* ``DIR1`` – path to the first directory containing CSV/TXT files
* ``DIR2`` – path to the second directory containing CSV/TXT files
* ``OUTPUT`` – path to write the comparison report (defaults to
  ``header_comparison.csv`` in the current working directory)
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


VALID_EXTENSIONS = {".csv", ".txt"}


@dataclass
class ComparisonResult:
    """Container representing the outcome of comparing two files."""

    filename: str
    status: str
    details: str = ""


def read_headers(file_path: Path) -> List[str]:
    """Return the header row from ``file_path`` as a list of strings.

    The function treats the first row in the file as the header.  Leading and
    trailing whitespace is stripped from each header element.
    """

    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            headers = next(reader)
        except StopIteration:
            # Empty file – treat as having no headers.
            return []
    return [header.strip() for header in headers]


def find_files(directory: Path) -> dict[str, Path]:
    """Return mapping of filename to :class:`Path` for allowed extensions."""

    files: dict[str, Path] = {}
    for path in directory.iterdir():
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
            files[path.name] = path
    return files


def compare_headers(dir1: Path, dir2: Path) -> List[ComparisonResult]:
    """Compare headers for matching files in ``dir1`` and ``dir2``."""

    dir1_files = find_files(dir1)
    dir2_files = find_files(dir2)

    results: List[ComparisonResult] = []
    all_filenames = sorted(set(dir1_files) | set(dir2_files))

    for filename in all_filenames:
        file1 = dir1_files.get(filename)
        file2 = dir2_files.get(filename)

        if file1 is None:
            results.append(
                ComparisonResult(
                    filename=filename,
                    status="missing",
                    details=f"{filename} not found in {dir1}",
                )
            )
            continue

        if file2 is None:
            results.append(
                ComparisonResult(
                    filename=filename,
                    status="missing",
                    details=f"{filename} not found in {dir2}",
                )
            )
            continue

        headers1 = read_headers(file1)
        headers2 = read_headers(file2)

        missing_in_dir2 = [header for header in headers1 if header not in headers2]
        missing_in_dir1 = [header for header in headers2 if header not in headers1]

        if not missing_in_dir1 and not missing_in_dir2:
            results.append(
                ComparisonResult(filename=filename, status="match", details="")
            )
            continue

        message_parts: List[str] = []
        if missing_in_dir2:
            message_parts.append(
                "Dir1 headers missing in Dir2: "
                + ", ".join(f"'{header}'" for header in missing_in_dir2)
            )
        if missing_in_dir1:
            message_parts.append(
                "Dir2 headers missing in Dir1: "
                + ", ".join(f"'{header}'" for header in missing_in_dir1)
            )

        results.append(
            ComparisonResult(
                filename=filename,
                status="mismatch",
                details="; ".join(message_parts),
            )
        )

    return results


def write_report(results: Sequence[ComparisonResult], output_path: Path) -> None:
    """Write the comparison results to ``output_path`` as CSV."""

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["filename", "status", "details"])
        for result in results:
            writer.writerow([result.filename, result.status, result.details])


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dir1", type=Path, help="First directory containing CSV/TXT files")
    parser.add_argument("dir2", type=Path, help="Second directory containing CSV/TXT files")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("header_comparison.csv"),
        help="Path to the output CSV file",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    dir1: Path = args.dir1
    dir2: Path = args.dir2
    output: Path = args.output

    if not dir1.is_dir():
        raise SystemExit(f"Directory not found: {dir1}")
    if not dir2.is_dir():
        raise SystemExit(f"Directory not found: {dir2}")

    results = compare_headers(dir1, dir2)
    write_report(results, output)


if __name__ == "__main__":
    main()
