from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

BASE_URL = "https://api.elsevier.com"
SEARCH_URL = f"{BASE_URL}/content/search/scopus"


class ElsevierClient:
    def __init__(self, api_key: str | None = None, inst_token: str | None = None) -> None:
        load_dotenv()
        self.api_key = api_key or os.getenv("ELSEVIER_API_KEY")
        self.inst_token = inst_token or os.getenv("ELSEVIER_INST_TOKEN")
        if not self.api_key:
            raise RuntimeError(
                "Missing ELSEVIER_API_KEY. Add it to a .env file or export it in your shell."
            )

    @property
    def json_headers(self) -> dict[str, str]:
        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json",
        }
        if self.inst_token:
            headers["X-ELS-Insttoken"] = self.inst_token
        return headers

    @property
    def xml_headers(self) -> dict[str, str]:
        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/xml",
        }
        if self.inst_token:
            headers["X-ELS-Insttoken"] = self.inst_token
        return headers

    def safe_get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        *,
        accept: str = "json",
        max_retry: int = 6,
        timeout: int = 60,
    ) -> requests.Response:
        headers = self.json_headers if accept == "json" else self.xml_headers
        backoff = 1.5

        for attempt in range(max_retry):
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            if response.status_code == 200:
                return response

            if response.status_code in (429, 500, 502, 503, 504):
                wait = backoff**attempt
                print(f"[WARN] HTTP {response.status_code}, retrying in {wait:.1f}s")
                time.sleep(wait)
                continue

            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")

        raise RuntimeError("Exceeded maximum retries.")

    def scopus_search_all(
        self,
        query: str,
        *,
        count: int = 25,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        start = 0
        seen_eid: set[str] = set()
        results: list[dict[str, Any]] = []

        while True:
            params = {
                "query": query,
                "count": count,
                "start": start,
                "view": "STANDARD",
            }
            data = self.safe_get(SEARCH_URL, params=params, accept="json").json()
            search_results = data.get("search-results", {})
            entries = search_results.get("entry", []) or []
            if not entries:
                break

            for entry in entries:
                record = extract_entry(entry)
                eid = record.get("eid")
                if eid and eid not in seen_eid:
                    seen_eid.add(eid)
                    results.append(record)

            total = int(search_results.get("opensearch:totalResults", "0") or 0)
            start += count
            print(f"[INFO] fetched {len(results)} / total {total} (start={start})")

            if max_records and len(results) >= max_records:
                return results[:max_records]
            if start >= total:
                break

            time.sleep(0.2)

        return results

    def download_article_xml(self, doi: str, output_dir: str | Path) -> Path | None:
        safe_name = doi.replace("/", "_").strip()
        if not safe_name:
            return None

        output_path = Path(output_dir) / f"{safe_name}.xml"
        url = f"{BASE_URL}/content/article/doi/{doi}"
        response = self.safe_get(url, accept="xml")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        return output_path

    def download_xml_from_csv(
        self,
        csv_path: str | Path,
        output_dir: str | Path,
        *,
        start: int = 0,
        end: int | None = None,
        delay_seconds: float = 0.2,
    ) -> list[Path]:
        dataframe = pd.read_csv(csv_path)
        dois = [str(value).strip() for value in dataframe["doi"].dropna().tolist()]
        sliced_dois = dois[start:end]

        downloaded: list[Path] = []
        for doi in sliced_dois:
            try:
                saved_path = self.download_article_xml(doi, output_dir)
                if saved_path:
                    downloaded.append(saved_path)
                    print(f"[OK] downloaded {doi}")
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] failed to download {doi}: {exc}")
            time.sleep(delay_seconds)

        return downloaded


def extract_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "eid": entry.get("eid"),
        "doi": entry.get("prism:doi"),
        "title": entry.get("dc:title"),
        "coverDate": entry.get("prism:coverDate"),
        "year": (entry.get("prism:coverDate") or "")[:4] if entry.get("prism:coverDate") else None,
        "publicationName": entry.get("prism:publicationName"),
        "issn": entry.get("prism:issn"),
        "volume": entry.get("prism:volume"),
        "issueIdentifier": entry.get("prism:issueIdentifier"),
        "pageRange": entry.get("prism:pageRange"),
        "citedby_count": entry.get("citedby-count"),
        "type": entry.get("subtypeDescription") or entry.get("prism:aggregationType"),
        "authors": entry.get("dc:creator"),
        "link_scopus": next(
            (link.get("@href") for link in entry.get("link", []) if link.get("@ref") == "scopus"),
            None,
        ),
    }


def save_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def save_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
