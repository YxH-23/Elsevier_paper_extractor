from __future__ import annotations

import argparse
from pathlib import Path

from elsevier_paper_extractor.client import ElsevierClient, save_csv, save_jsonl

DEFAULT_QUERY = (
    'TITLE-ABS-KEY( polysaccharide OR glycan OR glycans OR "glycosaminoglycan" '
    'OR GAG OR chitosan OR cellulose OR alginate OR hyaluronan ) '
    'AND TITLE-ABS-KEY( modulus OR tensile OR "Young*" OR rheology OR viscosity '
    'OR "storage modulus" OR "loss modulus" OR Tg OR DSC OR TGA OR swelling )'
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search Scopus and download Elsevier XML files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search Scopus and save results.")
    search_parser.add_argument("--query", default=DEFAULT_QUERY, help="Scopus query string.")
    search_parser.add_argument("--count", type=int, default=25, help="Records per API request.")
    search_parser.add_argument("--max-records", type=int, default=200, help="Maximum records to save.")
    search_parser.add_argument(
        "--output-dir",
        default="scopus_dump",
        help="Directory for CSV and JSONL outputs.",
    )

    xml_parser = subparsers.add_parser("download-xml", help="Download article XML files from a CSV DOI list.")
    xml_parser.add_argument("--csv-path", default="scopus_dump/scopus_search.csv", help="CSV file containing a doi column.")
    xml_parser.add_argument("--output-dir", default="papers_xml", help="Directory for XML files.")
    xml_parser.add_argument("--start", type=int, default=0, help="Start index for DOI slicing.")
    xml_parser.add_argument("--end", type=int, default=None, help="End index for DOI slicing.")
    xml_parser.add_argument("--delay", type=float, default=0.2, help="Delay between requests in seconds.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    client = ElsevierClient()

    if args.command == "search":
        rows = client.scopus_search_all(
            args.query,
            count=args.count,
            max_records=args.max_records,
        )
        output_dir = Path(args.output_dir)
        save_jsonl(output_dir / "scopus_search.jsonl", rows)
        save_csv(output_dir / "scopus_search.csv", rows)
        print(f"[DONE] saved {len(rows)} records to {output_dir}")
        return

    if args.command == "download-xml":
        downloaded = client.download_xml_from_csv(
            args.csv_path,
            args.output_dir,
            start=args.start,
            end=args.end,
            delay_seconds=args.delay,
        )
        print(f"[DONE] downloaded {len(downloaded)} XML files into {args.output_dir}")
        return

    raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
