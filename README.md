# FMH_Aud2Ins_GraphQl_S3

## Table of Contents
- Project Overview
- Technical Specifications
- Setup and Installation
- Code Structure
- Functionality
- API Documentation
- Testing
- Deployment
- User Guide
- Future Enhancements
- Appendices

## Project Overview

This repository provides utilities to fetch call transcription and recording metadata from a GraphQL endpoint, download associated audio recordings from S3 URLs, process audio files, and produce consolidated Excel output for analysis. It is designed for developers and data engineers who need to integrate call transcription data with recordings and downstream processing (e.g., audio analytics, speech-to-text verification, or manual review).

Purpose and objectives:
- Fetch call/transcription metadata from a GraphQL API.
- Extract S3 recording URLs from responses and download audio files.
- Process audio files (integration point with existing audio-processing code).
- Generate reference outputs (Excel) and persist results (e.g., MongoDB insertion hooks present).

Target audience and end-users:
- Developers integrating GraphQL-sourced call data with audio archives.
- Data engineers preparing recordings for speech analysis or archiving.
- QA engineers and stakeholders who want Excel reports combining metadata and processed results.

## Technical Specifications

- Language: Python 3.8+
- Primary libraries used or expected: requests, shutil (stdlib), json (stdlib), os (stdlib). Optional libraries used by downstream modules may include boto3 or pymongo when interacting with AWS or MongoDB.
- Files that act as entry points: `main.py`, `graphql_fetch.py`, `download_recordings.py`.

System architecture (high level):

- GraphQL API -> fetch metadata (call & recordings) using `graphql_fetch.py`
- Extract S3 URLs -> `download_recordings.py` extracts and downloads files
- Audio processing -> `gemini_processing.py` (process_audio_file integration)
- Excel/report generation -> `creating_reference_excel.py` and comparison/mongo insertion via `compare.py`

Dependencies and installation (see Setup below for commands).

## Setup and Installation

Prerequisites:
- Windows, macOS, or Linux with Python 3.8+ installed.
- Network access to the GraphQL endpoint (ngrok/remote URL) and to S3 URLs in responses.

1) Clone or open this repository in your workspace.

2) Create a virtual environment and activate it (PowerShell example):

```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
```

3) Install Python dependencies:

```powershell
pip install -r requirements.txt
```

If you don't have a `requirements.txt` yet or want to pin versions, create one from your environment with:

```powershell
pip freeze > requirements.txt
```

Common issues and solutions:
- `requests` not found: ensure virtual environment is active and run `pip install requests`.
- Permission on PowerShell activation: if you get an execution policy error, run PowerShell as Administrator and consider `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.
- Network errors when downloading files: confirm the GraphQL endpoint and returned S3 URLs are accessible from your network.

## Code Structure

Top-level files and directories (extracted from the repository):

- `main.py` — Orchestrator script that demonstrates end-to-end usage: fetch GraphQL data, extract S3 URLs, download recordings, process audio files, and produce combined Excel outputs.
- `graphql_fetch.py` — Contains `fetch_call_data_transcribe(...)`. Sends a GraphQL POST request and returns a list of call data dictionaries.
- `download_recordings.py` — Utilities to parse nested GraphQL responses (`extract_s3_urls_with_callid`), clear/download to `downloads/`, and `download_files(...)` which streams files to disk.
- `gemini_processing.py` — Audio processing hooks (project-specific). `main.py` imports `process_audio_file` from there.
- `creating_reference_excel.py` — Utilities to create Excel outputs by combining MongoDB rows and GraphQL data (entry: `process_s_id`).
- `compare.py` — Contains a `mongo_insert` helper used in `main.py` to persist or compare outputs.
- `parse.py`, `process_audio.py`, `fetch_by_date.py`, `download_by_date.py` — Supporting scripts (scheduling, targeted downloads, and parsing utilities).
- `recordings/` and `downloads/` — Local storage folders for original and downloaded audio files.

Coding standards and conventions:
- Keep functions small, single-responsibility, and well-documented with docstrings.
- Use safe dictionary lookups (get()) when parsing external data.
- Log or print clear messages for success/failure, including helpful icons used in the repo (✅, ❌, ⚠️).

## Functionality

Key features:
- Fetch call transcription and metadata via GraphQL using `fetch_call_data_transcribe()`.
- Recursively extract recording S3 URLs and associated call IDs from nested GraphQL responses.
- Download recordings to a local directory with `download_files()` which streams content to disk.
- Process downloaded audio via `process_audio_file()` (project-specific audio processing).
- Produce combined Excel reports and optionally insert or compare records in MongoDB.

Detailed usage examples:

- Fetch data and print:

```powershell
python graphql_fetch.py
```

- Download all recordings and process (example shown in `main.py`):

```powershell
python main.py
```

- Use `download_recordings.py` directly to download files after getting the JSON result from `fetch_call_data_transcribe`.

Notes on the user interface:
- This project provides CLI-style scripts (no GUI). For interactive use, run individual scripts or import functions in your own tooling.

## API Documentation

GraphQL usage (from `graphql_fetch.py`):

- Function: `fetch_call_data_transcribe(url, from_date, to_date, limit)`
  - url (str): GraphQL endpoint, default is a demo ngrok URL in the file.
  - from_date / to_date (str): Date strings (the function currently formats a default based on today's date).
  - limit (int): How many results to return.
  - Returns: list of dictionaries, where each dict contains fields such as `callId`, `entityName`, `Recordings` (with `s3Url` and `dateCreatedInUpdates`).

Example response fragment (shape):

```json
{
  "callId": "abcd1234",
  "entityName": "Example",
  "Recordings": [
    {"s3Url": "https://s3.amazonaws.com/.../file.mp3", "dateCreatedInUpdates": "2025-10-01T..."}
  ]
}
```

Authentication and authorization:
- The current code assumes a public or proxied GraphQL endpoint (no auth headers). If your endpoint requires auth, modify `graphql_fetch.py` to add an `Authorization` header (Bearer token, API key, etc.) inside the `headers` dict.

Error handling and status codes:
- `graphql_fetch.py` prints a ❌ message when the response status is not 200. It returns an empty list in that case.
- `download_recordings.py` prints warnings for failed downloads and returns the list of successfully downloaded files.

## Testing

Testing framework and methodology:
- The repository contains small test scripts like `test.py` and `referencefiletest.py`. No centralized `pytest` or `unittest` harness is mandated—adding one is a recommended improvement.

How to run tests (basic):

```powershell
python test.py
# or
python -m unittest discover -v
```

Code coverage:
- There is no coverage tool configured by default. To collect coverage, install `coverage` and run:

```powershell
pip install coverage
coverage run -m pytest
coverage report -m
```

## Deployment

Environments:
- Development: run locally with the sample ngrok endpoint.
- Staging/Production: update the GraphQL endpoint to the canonical HTTPS endpoint and ensure S3 access/credentials are in place.

Deployment steps (simple, manual):
1. Ensure dependencies are installed in the target environment.
2. Update configuration/environment variables (GraphQL URL, API keys, credentials for S3 if private).
3. Run `python main.py` or wire into a scheduled job (cron, Windows Task Scheduler).

CI/CD:
- No CI/CD is currently configured. Recommended: add a GitHub Actions workflow that runs linters, unit tests, and optionally pushes artifacts.

Rollback and contingency:
- Keep backups of `downloads/` and any persisted MongoDB exports.
- If a remote endpoint breaks, revert the endpoint configuration or route traffic to a read-only snapshot.

## User Guide

Getting started (short):
1. Activate environment and install deps.
2. Confirm your GraphQL endpoint is reachable.
3. Run `python main.py` to perform a full example flow.

Troubleshooting tips and FAQs:
- Q: Files are not downloading. A: Check the returned `s3Url` values are valid and reachable. Confirm network access and that the URLs are not presigned expired links.
- Q: Authentication failure. A: Add the required auth headers to `graphql_fetch.py` and verify credentials.
- Q: PowerShell activation blocked. A: Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` as needed.

Support contact:
- For internal projects: add team contact info here (email, Slack). For now, open an issue in the repository for help and provide logs and reproduction steps.

## Future Enhancements

- Add a configuration file (YAML/JSON) or environment variable support for endpoints, credentials, and paths.
- Replace prints with a structured logger (Python `logging`) and log levels.
- Add unit tests and CI integration (GitHub Actions) with automated coverage.
- Add a safe retry/backoff for downloads and GraphQL requests.
- Add support for private S3 access (boto3 presigned URL generation or direct authenticated downloads).

## Appendices

- Additional resources:
  - GraphQL docs: https://graphql.org/learn/
  - requests (HTTP for Python): https://docs.python-requests.org/

- Glossary:
  - GraphQL: Query language used to fetch structured data.
  - S3: AWS Simple Storage Service, used here as the storage for recordings.
  - s_id/callId: Identifier used to match recordings to metadata.

---

If you'd like, I can also:
- Add more granular examples (sample expected JSON payloads).
- Create a formal `requirements.txt` pinned to specific package versions after scanning imports across the repo.
- Add a GitHub Actions CI configuration to run tests and linting on push.

Short completion summary: README.md created with full project documentation. See `requirements.txt` for minimal installs.
