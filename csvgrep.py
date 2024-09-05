#!/usr/bin/env python3

"""
Read in a CSV, dump any lines that match (or don't match) the provided regex on the line (or on the specified column).

Allows grepping a CSV that has multiline fields, which is not supported by raw grep.
"""

from defusedcsv import csv
import argparse
import re
import logging

LOG = logging.getLogger(__name__)
ANY_COLUMN = -1


def add_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "match",
        type=str,
        help="The regex to match.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=argparse.FileType("r"),
        default="-",
        help="Input CSV file. Default is stdin.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w"),
        default="-",
        help="Output CSV file. Default is stdout.",
    )
    parser.add_argument(
        "-c",
        "--column",
        type=int,
        default=ANY_COLUMN,
        help="The column to grep on, 0-indexed. Default is -1, which greps all columns.",
    )
    parser.add_argument(
        "-n",
        "--no-header",
        action="store_true",
        help="If set, the first line of the input CSV will be treated as data, not a header.",
    )
    parser.add_argument(
        "-V",
        "--invert-match",
        action="store_true",
        help="Invert the match. If set, lines that do not match will be dumped.",
    )
    parser.add_argument(
        "-F",
        "--fixed-strings",
        action="store_true",
        help="Interpret the match as a fixed string, not a regex.",
    )
    parser.add_argument(
        "--field-size-limit",
        type=int,
        default=csv.field_size_limit(),
        help="The maximum size of a single CSV field.",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_args(parser)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    if csv.field_size_limit() < args.field_size_limit:
        csv.field_size_limit(args.field_size_limit)

    reader = csv.reader(args.input)
    writer = csv.writer(args.output)

    if args.fixed_strings:
        regex = re.compile(re.escape(args.match))
    else:
        regex = re.compile(args.match)

    LOG.debug("Using regex: %s", regex.pattern)

    first_row = True
    lines = 0

    for row in reader:
        if first_row:
            first_row = False
            if args.column != ANY_COLUMN and args.column >= len(row):
                LOG.error("First row %s has fewer columns than %s, cannot match on that column", row, args.column)
                return
            if not args.no_header:
                writer.writerow(row)
                continue

        if args.column == ANY_COLUMN:
            # match the regex on any column
            if args.invert_match:
                if not any(regex.search(cell) for cell in row):
                    writer.writerow(row)
                    lines += 1
            elif any(regex.search(cell) for cell in row):
                writer.writerow(row)
                lines += 1
        else:
            # match the regex on the specified column
            if args.invert_match:
                if not regex.search(row[args.column]):
                    writer.writerow(row)
                    lines += 1
            elif regex.search(row[args.column]):
                writer.writerow(row)
                lines += 1

    LOG.info("Matched %s rows", lines)

if __name__ == "__main__":
    main()
