# Elsevier Paper Extractor

This project turns an exploratory notebook into a small Python package for:

- searching Scopus records with the Elsevier API
- exporting search results as CSV or JSONL
- downloading article XML files from a DOI list

The original notebook is kept in [`notebooks/notebook.ipynb`](./notebooks/notebook.ipynb), while the reusable logic now lives in `src/`.

## Project structure

```text
.
├── notebooks/
│   └── notebook.ipynb
├── src/
│   └── elsevier_paper_extractor/
│       ├── __init__.py
│       ├── cli.py
│       └── client.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Requirements

- Python 3.10+
- an Elsevier API key

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Then edit `.env` and add your key:

```bash
ELSEVIER_API_KEY=your_api_key_here
ELSEVIER_INST_TOKEN=
```

You can also export these variables directly in your shell.

## Usage

### 1. Search Scopus and save results

```bash
python -m elsevier_paper_extractor.cli search \
  --query 'TITLE-ABS-KEY(polysaccharide OR glycan) AND TITLE-ABS-KEY(modulus OR rheology)' \
  --max-records 200 \
  --output-dir scopus_dump
```

This creates:

- `scopus_dump/scopus_search.csv`
- `scopus_dump/scopus_search.jsonl`

### 2. Download article XML files from a CSV file

```bash
python -m elsevier_paper_extractor.cli download-xml \
  --csv-path scopus_dump/scopus_search.csv \
  --output-dir papers_xml \
  --start 11 \
  --end 100
```

This reads DOI values from the CSV file and downloads each paper as an XML file.

## Notes for GitHub

- Do not commit your real API key.
- Generated outputs such as `scopus_dump/` and `papers_xml/` are ignored by default.
- If you want to share example outputs, add a small sanitized sample folder instead of your full raw export.

## Suggested next steps

- initialize git with `git init`
- create a GitHub repository
- push with `git remote add origin ...` and `git push -u origin main`
