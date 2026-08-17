# 🗂️ DocVault — Supabase Document Management CRUD App

A full-stack document management application built to demonstrate **Supabase
PostgreSQL**, **Supabase Storage**, and **Supabase Edge Functions** working
together from a **Python** backend, with a modern **Streamlit** UI and a
parallel **terminal CLI**.

> 🆕 **First time with Supabase?** Read [`SUPABASE_GUIDE.md`](./SUPABASE_GUIDE.md)
> first — it explains every concept in this project from zero, with
> click-by-click dashboard instructions.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Supabase Setup](#supabase-setup)
- [Running Locally](#running-locally)
- [CLI Usage](#cli-usage)
- [Edge Function Deployment](#edge-function-deployment)
- [CRUD Operations Reference](#crud-operations-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)

---

## Features

- 📤 **Upload** documents with drag-and-drop, metadata, and server-side validation
- 📋 **List / browse** documents with search and category filtering
- ✏️ **Edit** metadata (description, category) without touching the file
- 🔁 **Replace** the underlying file while keeping the same document record
- 🗑️ **Delete** with a confirmation dialog, cleaning up both Storage and the database
- ⚡ **Edge Function** (`validate-document`) that validates file type/size server-side
  and returns a normalized category + validation tag
- 🖥️ **Terminal CLI** (`cli.py`) that performs every CRUD operation with no UI
- 🎨 Modern, minimal, dark-themed dashboard UI (Streamlit + custom CSS)
- 🛡️ Proper error handling, loading states, empty states, and confirmation dialogs
- 🔒 Credentials only in environment variables — nothing hardcoded

## Tech Stack

| Layer               | Technology                          |
|----------------------|--------------------------------------|
| Frontend UI          | Streamlit + custom CSS               |
| Backend language     | Python 3.10+                         |
| Supabase SDK         | `supabase-py`                        |
| Database             | Supabase PostgreSQL                  |
| File storage         | Supabase Storage                     |
| Serverless functions | Supabase Edge Functions (Deno + TS)  |
| Terminal interface   | Python `argparse` CLI (`cli.py`)     |

## Architecture

```text
                 ┌────────────────────┐
   User  ─────▶  │   Streamlit UI /    │
                 │        CLI          │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │ document_service.py │   <- single source of truth
                 │  (Python business   │      for all CRUD logic
                 │   logic layer)      │
                 └──────────┬──────────┘
                             │
          ┌──────────────────┼───────────────────┐
          ▼                  ▼                    ▼
 ┌─────────────────┐ ┌───────────────┐  ┌────────────────────┐
 │ Supabase Storage │ │  Supabase     │  │  Supabase Edge      │
 │ (raw file bytes) │ │  PostgreSQL   │  │  Function            │
 │                   │ │  (metadata)   │  │  validate-document   │
 └─────────────────┘ └───────────────┘  └────────────────────┘
```

Both the Streamlit UI and the CLI call the exact same functions in
`app/document_service.py`, so behavior never diverges between them. See
`SUPABASE_GUIDE.md` Part 2 for a full walkthrough of this architecture and
the upload flow.

## Project Structure

```text
supabase-crud-app/
│
├── app/
│   ├── streamlit_app.py       # Streamlit UI (pages, layout, styling)
│   ├── document_service.py    # Core CRUD logic (Storage + DB + Edge Fn)
│   ├── supabase_client.py     # Shared Supabase client
│   ├── edge_function_client.py# HTTP wrapper for the Edge Function
│   ├── config.py               # Loads and validates environment variables
│   └── utils.py                # Formatting helpers (size, date, icons)
│
├── supabase/
│   └── functions/
│       └── validate-document/
│           └── index.ts        # Edge Function source (Deno/TypeScript)
│
├── database/
│   └── schema.sql              # `documents` table + RLS policy + trigger
│
├── tests/
│   └── MANUAL_TESTING.md       # Manual test checklist for every feature
│
├── cli.py                      # Terminal CRUD tool (no UI)
├── .env.example                 # Environment variable template
├── .gitignore
├── requirements.txt
├── README.md                    # You are here
└── SUPABASE_GUIDE.md            # Complete beginner's guide to Supabase
```

## Installation

### Prerequisites

- Python 3.10 or newer
- A free [Supabase](https://supabase.com) account
- (Optional, for deploying the Edge Function) [Node.js](https://nodejs.org) — used to run the Supabase CLI via `npx`

### 1. Clone / download the project

```bash
cd supabase-crud-app
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (cmd.exe):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Copy the example file and fill in your real Supabase credentials:

```bash
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
```

| Variable                     | Where to find it                                                    |
|-------------------------------|-----------------------------------------------------------------------|
| `SUPABASE_URL`                 | Dashboard → Project Settings → API → Project URL                     |
| `SUPABASE_ANON_KEY`            | Dashboard → Project Settings → API → Project API keys → `anon public` |
| `SUPABASE_SERVICE_ROLE_KEY`    | Dashboard → Project Settings → API → Project API keys → `service_role`|
| `STORAGE_BUCKET`               | The bucket name you create (default: `documents`)                    |
| `EDGE_FUNCTION_NAME`           | Name of the deployed Edge Function (default: `validate-document`)    |
| `MAX_FILE_SIZE_MB`             | Client-side size limit, should match the Edge Function's limit (20)  |

⚠️ **Never commit `.env`.** It's already in `.gitignore`. Full explanation of
each key's purpose and security implications is in `SUPABASE_GUIDE.md` Part 4.

## Supabase Setup

Full click-by-click instructions are in `SUPABASE_GUIDE.md` Parts 3, 5, and 6.
Quick summary:

1. Create a Supabase project at [supabase.com](https://supabase.com).
2. Open the **SQL Editor** and run the contents of `database/schema.sql`.
3. Open **Storage** and create a new bucket named `documents`.
4. Copy your Project URL and API keys into `.env`.
5. Deploy the Edge Function (see [below](#edge-function-deployment)).

## Running Locally

### Run the Streamlit UI

```bash
streamlit run app/streamlit_app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

### Run the CLI

```bash
python cli.py list
```

See [CLI Usage](#cli-usage) below for the full command reference.

## CLI Usage

```bash
python cli.py upload <path> [--description TEXT] [--category TEXT]
python cli.py list [--category TEXT]
python cli.py show <document_id>
python cli.py download <document_id> [--out PATH]
python cli.py update <document_id> [--description TEXT] [--category TEXT]
python cli.py replace <document_id> <new_file_path>
python cli.py delete <document_id> [--yes]
```

**Examples:**

```bash
python cli.py upload ./sample.pdf --description "Q3 report" --category Finance
python cli.py list
python cli.py list --category Finance
python cli.py show 3fa85f64-5717-4562-b3fc-2c963f66afa6
python cli.py download 3fa85f64-5717-4562-b3fc-2c963f66afa6 --out ./downloaded.pdf
python cli.py update 3fa85f64-5717-4562-b3fc-2c963f66afa6 --description "Updated Q3 report"
python cli.py replace 3fa85f64-5717-4562-b3fc-2c963f66afa6 ./new_version.pdf
python cli.py delete 3fa85f64-5717-4562-b3fc-2c963f66afa6 --yes
```

## Edge Function Deployment

Full explanation in `SUPABASE_GUIDE.md` Part 14. Quick reference:

```bash
# Install/run the Supabase CLI (via npx, no global install needed)
npx supabase login
npx supabase init
npx supabase link --project-ref <your-project-ref>

# Deploy the function that already exists in supabase/functions/validate-document
npx supabase functions deploy validate-document
```

Test it directly with `curl` once deployed:

```bash
curl -X POST "https://<your-project-ref>.supabase.co/functions/v1/validate-document" \
  -H "Authorization: Bearer <your-service-role-key>" \
  -H "Content-Type: application/json" \
  -d '{"file_name":"test.pdf","file_type":"application/pdf","file_size":1024,"category":"finance"}'
```

## CRUD Operations Reference

| Operation | Storage                          | Database                         | Edge Function        |
|-----------|-----------------------------------|-----------------------------------|------------------------|
| Create    | Upload file bytes                 | Insert metadata row               | ✅ Validates before upload |
| Read      | Download file bytes / signed URL  | Select rows                       | —                      |
| Update    | Replace file (new path)           | Update metadata / storage_path    | ✅ Re-validates on replace |
| Delete    | Remove file object                | Delete row                        | —                      |

See `SUPABASE_GUIDE.md` Part 16 for the full explanation of each operation,
including how Storage/Database consistency is maintained on partial failure.

## Testing

See [`tests/MANUAL_TESTING.md`](./tests/MANUAL_TESTING.md) for a full manual
test checklist covering every feature, including invalid file types,
oversized files, and Edge Function failure scenarios.

## Troubleshooting

See `SUPABASE_GUIDE.md` Part 17 for a complete "Problem → Why → Fix" guide
covering invalid API keys, missing buckets, Edge Function deployment issues,
RLS/policy errors, and more.

## Future Improvements

- User authentication (Supabase Auth) with per-user document ownership
- Full-text search over document descriptions
- File preview (PDF/image thumbnails) inside the UI
- Pagination for large document lists
- Versioned file history instead of overwrite-on-replace
- Automated test suite (pytest) with a Supabase test project
