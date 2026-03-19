# Elsevier Paper Extractor

This project packages the original notebook into a simpler command-line tool for:

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
ELSEVIER_INST_TOKEN= #Optioal
```

The program now reads `.env` automatically, so you do not need to export variables manually.

## Easiest usage

Install once, fill in `.env`, then run:

```bash
elsevier-extractor --help
```

## Main commands

### 1. Search Scopus and save results

```bash
elsevier-extractor search \
  --query 'TITLE-ABS-KEY(polysaccharide OR glycan) AND TITLE-ABS-KEY(modulus OR rheology)' \
  --max-records 200
```

This creates `scopus_dump/scopus_search.csv` and `scopus_dump/scopus_search.jsonl`.

### 2. Download XML from the generated CSV

```bash
elsevier-extractor download-xml \
  --start 11 \
  --end 100
```

This reads `scopus_dump/scopus_search.csv` by default and saves XML files into `papers_xml/`.

### 3. Run the whole workflow in one command

```bash
elsevier-extractor run-all \
  --query 'TITLE-ABS-KEY(polysaccharide OR glycan) AND TITLE-ABS-KEY(modulus OR rheology)' \
  --max-records 50 \
  --start 0 \
  --end 20
```

This will:

- search Scopus
- save CSV and JSONL files
- download XML files for the selected DOI range

## Notes for GitHub

- Do not commit your real API key.
- Generated outputs such as `scopus_dump/` and `papers_xml/` are ignored by default.
- If you want to share example outputs, add a small sanitized sample folder instead of your full raw export.
