# 📘 The Complete Beginner's Guide to This Supabase Project

This guide assumes you have **never used Supabase before**. Every concept is
explained from zero, with examples from this exact project. Read it top to
bottom the first time; use it as a reference afterward.

---

## Table of Contents

- [Part 1 — What is Supabase?](#part-1--what-is-supabase)
- [Part 2 — Project Architecture](#part-2--project-architecture)
- [Part 3 — Creating the Supabase Project](#part-3--creating-the-supabase-project)
- [Part 4 — Getting API Keys](#part-4--getting-api-keys)
- [Part 5 — Database Setup](#part-5--database-setup)
- [Part 6 — Storage Setup](#part-6--storage-setup)
- [Part 7 — Python Setup](#part-7--python-setup)
- [Part 8 — Understanding the Python Code](#part-8--understanding-the-python-code)
- [Part 9 — Edge Functions Explained from Zero](#part-9--edge-functions-explained-from-zero)
- [Part 10 — Complete End-to-End Flow](#part-10--complete-end-to-end-flow)
- [Part 11 — CRUD Explained in Detail](#part-11--crud-explained-in-detail)
- [Part 12 — Troubleshooting](#part-12--troubleshooting)
- [Part 13 — Concepts to Understand Before Presenting](#part-13--concepts-to-understand-before-presenting)

---

## Part 1 — What is Supabase?

**Supabase** is a company/platform that gives you a ready-made backend so you
don't have to build one from scratch. When you create a Supabase project, you
instantly get:

1. A real **PostgreSQL database** (a full relational database, not a toy).
2. **File Storage** for uploading/downloading files (images, PDFs, etc).
3. **Edge Functions** — small pieces of server-side code you can deploy without
   managing a server.
4. **Authentication** (login/signup) — not used in this project, but available.
5. Auto-generated **APIs** for your database, so apps can talk to it directly.

### Why are we using it?

Normally, building "upload a file and save info about it" requires you to:
run a server, run a database, write file-upload code, handle security, etc.
Supabase provides all of that as a managed service, so this project can focus
on **application logic** instead of **infrastructure**.

### Supabase vs. a traditional backend

A traditional backend means: you write a server (e.g. with Flask/Django/
Express), you host a database yourself, you manage file storage yourself
(e.g. AWS S3), and you're responsible for keeping all of it running and
secure. Supabase bundles the database, file storage, and serverless
functions into one managed platform, so a small project like this one needs
almost no custom server code — our Python app talks directly to Supabase.

### Supabase vs. Firebase

Firebase (Google's platform) is the most well-known comparable product.
The biggest practical difference: Firebase's primary database (Firestore) is
a NoSQL document database, while Supabase's database is standard PostgreSQL —
a mature, SQL-based relational database used across the software industry.
If you already know SQL, or want to learn transferable database skills,
Supabase's approach is more directly applicable outside of Supabase itself.

### PostgreSQL, in one paragraph

PostgreSQL ("Postgres") is free, open-source relational database software.
"Relational" means data is organized into **tables** with **rows** and
**columns**, and tables can reference each other. In this project, we have
one table called `documents`, where each **row** is one uploaded file's
metadata, and each **column** is one piece of information about it (name,
size, type, etc).

### Storage, in one paragraph

Supabase Storage is a separate system for storing the actual **file bytes**
(the PDF, image, etc itself) — think of it like a specialized file cabinet
or cloud drive. It is intentionally **separate** from the database because
databases are optimized for structured, searchable data (rows/columns), not
for storing large binary blobs efficiently. See Part 6 for more detail on
why we keep these two systems separate but linked.

### Edge Functions, in one paragraph

An Edge Function is a small piece of server-side code (written in
TypeScript, run by Deno) that Supabase hosts and runs for you — you never
manage a server. It's called "serverless" because you don't provision or
maintain any server infrastructure; you just write a function and deploy it.
See Part 9 for a full deep-dive.

### APIs, in one paragraph

An API (Application Programming Interface) is how one piece of software asks
another piece of software to do something. Supabase automatically generates
a REST API for your database tables and gives you a client library
(`supabase-py` for Python) that talks to that API for you, so you write
Python function calls like `client.table("documents").select("*")` instead
of hand-writing raw HTTP requests.

---

## Part 2 — Project Architecture

### The high-level flow

```text
User
 ↓
Frontend (Streamlit UI or Terminal CLI)
 ↓
Python Backend (app/document_service.py)
 ↓
Supabase
 ├── PostgreSQL Database   (stores metadata: name, size, type, category...)
 ├── Storage                (stores the actual file bytes)
 └── Edge Function          (validates the file server-side)
```

**What happens at every step, in plain English:**

1. **User** interacts with either the Streamlit web page or types a command
   into the terminal CLI.
2. **Frontend** collects what the user wants to do (e.g. "upload this file
   with this description") and calls a Python function.
3. **Python Backend** (`document_service.py`) is the only code that actually
   talks to Supabase. It decides the ORDER of operations (validate, then
   upload to Storage, then insert into the Database) and handles errors.
4. **Supabase** does the actual work: PostgreSQL stores the metadata row,
   Storage stores the file bytes, and the Edge Function checks the file is
   allowed before anything is saved.

### The complete upload flow, step by step

```text
1. User picks a file in the UI (or passes a path to the CLI)
2. Python reads the file's name, size, and guessed MIME type
3. Python calls the Edge Function over HTTPS with those 3 facts
4. Edge Function checks: is this file type allowed? Is it too big?
   -> If NOT valid: returns an error, Python stops here and shows it to the user
   -> If valid: returns a normalized category + a validation tag
5. Python uploads the raw file bytes to Supabase Storage
6. Python inserts a new row into the "documents" table in PostgreSQL,
   including the storage_path that points at the file we just uploaded
7. If step 6 fails, Python deletes the file from Storage (rollback),
   so we never have a file with no matching database row
8. The UI refreshes and shows the new document
```

This "validate → upload → insert, with rollback on failure" pattern is the
single most important piece of logic in the whole project — it's what keeps
Storage and the Database from drifting out of sync. It lives entirely inside
`upload_document()` in `app/document_service.py`.

---

## Part 3 — Creating the Supabase Project

> 🔧 **MANUAL STEP REQUIRED** — this part must be done by you in a browser;
> it can't be automated.

1. Go to [supabase.com](https://supabase.com) and click **Start your project**.
2. Sign up (GitHub login is the fastest option) or log in.
3. Click **New Project**.
4. Choose the **Organization** (create one if you don't have one yet — just
   give it any name, e.g. your name or "Personal").
5. Fill in:
   - **Project name** — e.g. `docvault-internship`
   - **Database Password** — click "Generate a password" and **save it
     somewhere safe** (a password manager or a temporary note). You won't
     need to type this password anywhere in this project's code, but you
     may need it later if you ever connect a raw Postgres client.
   - **Region** — pick the one closest to you for the best latency.
6. Click **Create new project**.
7. Wait 1–2 minutes while Supabase provisions your database. You'll land on
   the project **Dashboard** automatically when it's ready.
8. In the left sidebar, note these sections — you'll use them throughout
   this guide:
   - **Table Editor** — view/edit database rows visually
   - **SQL Editor** — run raw SQL (used in Part 5)
   - **Storage** — manage file buckets (used in Part 6)
   - **Edge Functions** — view deployed functions (used in Part 9)
   - **Project Settings → API** — find your URL and keys (used in Part 4)

---

## Part 4 — Getting API Keys

> 🔧 **MANUAL STEP REQUIRED**

1. In your project dashboard, click the **gear icon (⚙️ Project Settings)**
   in the bottom of the left sidebar.
2. Click **API** in the settings menu.
3. You'll see:
   - **Project URL** — looks like `https://abcdefghijklmno.supabase.co`.
     Copy this into `SUPABASE_URL` in your `.env` file.
   - **Project API keys** section with two keys:
     - **`anon` `public`** — copy into `SUPABASE_ANON_KEY`.
     - **`service_role`** — click "Reveal" then copy into
       `SUPABASE_SERVICE_ROLE_KEY`.

### Which key does what?

| Key | Where it's safe to use | What it can do |
|-----|--------------------------|------------------|
| **Project URL** | Anywhere | Just an address — not a secret by itself |
| **`anon` / public key** | Browser, mobile app, anywhere public | Limited by Row Level Security (RLS) rules you define |
| **`service_role` key** | ⚠️ Server-side ONLY, never in a browser | **Bypasses all RLS rules** — full read/write access to everything |

### Why does this project use the service_role key?

This is a single-user internship project with **no login system**, so there
is no "current user" for RLS policies to check against. Our Python code
(`app/supabase_client.py`) runs entirely on your machine/server — never
inside a user's browser — which makes it an appropriate, contained place to
use the service_role key. It is loaded only from your local `.env` file
(never committed to git, never sent to the Streamlit frontend's HTML/JS).

**Security risk if this key ever leaked:** anyone with it could read, modify,
or delete *any* row in *any* table and *any* file in Storage, completely
bypassing your security rules. Treat it like a database root password.

---

## Part 5 — Database Setup

> 🔧 **MANUAL STEP REQUIRED**

1. In your project dashboard, click **SQL Editor** in the left sidebar.
2. Click **New query**.
3. Open `database/schema.sql` from this repo, copy its **entire contents**,
   and paste it into the SQL Editor.
4. Click **Run** (or press Ctrl/Cmd+Enter).
5. You should see "Success. No rows returned." Go to **Table Editor** in the
   sidebar — you should now see a `documents` table.

### Explaining the SQL, line by line (concepts)

```sql
create extension if not exists "pgcrypto";
```
Turns on a Postgres add-on that lets the database generate random UUIDs for
us. Without this, `gen_random_uuid()` wouldn't exist.

```sql
id uuid primary key default gen_random_uuid(),
```
- **UUID** = Universally Unique Identifier — a random-looking ID like
  `3fa85f64-5717-4562-b3fc-2c963f66afa6`. We use this instead of simple
  numbers (1, 2, 3...) because UUIDs are safe to expose in URLs and APIs and
  don't reveal how many rows exist or let someone guess other IDs.
- **primary key** = the column that uniquely identifies each row. Every
  table should have one.
- **default gen_random_uuid()** = if we don't provide an `id` ourselves when
  inserting a row, Postgres generates one automatically.

```sql
storage_path text not null unique,
```
- **text** = a string data type (no length limit, unlike `varchar(n)`).
- **not null** = this field is required; Postgres refuses to save a row
  without it.
- **unique** = a **constraint** — Postgres will refuse to insert two rows
  with the same `storage_path`, protecting us from ever having two database
  rows pointing at the same file in Storage.

```sql
file_size bigint not null check (file_size >= 0),
```
- **bigint** = a large integer type, needed because file sizes in bytes can
  exceed what a normal 32-bit `int` can hold.
- **check (file_size >= 0)** = another constraint: Postgres will reject any
  row where this condition is false, protecting data integrity at the
  database level (not just in our Python code).

```sql
uploaded_at timestamptz not null default now(),
```
- **timestamptz** = "timestamp with time zone" — stores the exact moment in
  time, unambiguous no matter what timezone the server or user is in. This
  is the Postgres best practice over a plain `timestamp`.
- **default now()** = automatically set to the current time when a row is
  created, so we never have to set this manually in Python.

### Indexes

```sql
create index if not exists idx_documents_uploaded_at on public.documents (uploaded_at desc);
```
An **index** works like a book's table of contents: it lets Postgres jump
straight to the relevant rows instead of scanning the entire table. We add
one on `uploaded_at` because the "Recent Uploads" dashboard section sorts by
this column on every page load.

### The auto-update trigger

The SQL also creates a **trigger** — a rule that tells Postgres "whenever a
row in `documents` is updated, automatically set `updated_at` to right now."
This guarantees `updated_at` is always accurate, even if a future version of
the code forgets to set it manually.

### Row Level Security (RLS)

```sql
alter table public.documents enable row level security;
create policy "Allow all access to documents" on public.documents for all using (true) with check (true);
```
RLS is Postgres's row-by-row permission system. Supabase turns it **on** by
default for new tables, which means **all access is blocked** until you add
a policy. Since this project has no login system, we add one permissive
policy that allows all operations — but because RLS still applies, only
requests using the `service_role` key (which bypasses RLS) or a policy match
can succeed. This is why our Python app uses the service_role key.

---

## Part 6 — Storage Setup

> 🔧 **MANUAL STEP REQUIRED**

### What is a "bucket"?

A **bucket** is a named container inside Supabase Storage, similar to a
top-level folder — e.g. a bucket called `documents` might contain paths like
`2026/08/report.pdf`. Buckets let you group files and apply different rules
(public vs private) to different groups.

### Creating the bucket

1. In your project dashboard, click **Storage** in the left sidebar.
2. Click **New bucket**.
3. Name it exactly `documents` (matching `STORAGE_BUCKET` in `.env`).
4. Leave it **Private** (do not toggle "Public bucket"). Our app accesses
   files using the service_role key and generates temporary **signed URLs**
   for viewing, so the bucket does not need to be public.
5. Click **Create bucket**.

### Public vs. private buckets

- **Public bucket** — anyone with a file's URL can view/download it forever,
  no authentication needed. Convenient, but means anyone who discovers or
  guesses a URL can access the file.
- **Private bucket** (what we use) — files can only be accessed with a valid
  key, or a temporary **signed URL** that expires after a set time (we use 1
  hour, see `get_public_url()` in `document_service.py`). More secure, at
  the cost of slightly more code.

### Storage paths

A **storage path** is the file's "address" inside the bucket, e.g.
`2026/08/9f3a1c2b_invoice.pdf`. We generate these ourselves in
`_build_storage_path()` (in `document_service.py`) by combining the current
year/month with a random 8-character prefix and the original file name —
this guarantees two different uploads never overwrite each other, even if
both are named `invoice.pdf`.

### Why Storage is separate from PostgreSQL

Databases like Postgres are built and optimized for **structured, indexed,
searchable data** — rows and columns you filter, sort, and join. They are
not designed to efficiently store large binary blobs like a 15 MB PDF; doing
so bloats the database, slows down backups, and slows down every query that
touches that table. Storage systems (like Supabase Storage, or AWS S3) are
purpose-built for storing and serving large files efficiently. Keeping them
separate — file bytes in Storage, searchable metadata in the Database — and
linking them with a `storage_path` column is a standard, scalable pattern.

### Upload / Download / Replace / Delete, in this project

All four operations happen in `document_service.py` via the Supabase Python
client's `storage.from_(bucket)` methods:

```python
client.storage.from_("documents").upload(path=..., file=..., file_options=...)
client.storage.from_("documents").download(path)
client.storage.from_("documents").remove([path])
```

"Replace" isn't a single Storage operation — we **upload the new file to a
new path**, update the database row to point at the new path, then **remove
the old path**. See Part 11 for why this order matters.

---

## Part 7 — Python Setup

### 1. Install Python

Download Python 3.10+ from [python.org/downloads](https://www.python.org/downloads/)
and run the installer. **On Windows**, make sure you check "Add Python to
PATH" during installation.

Verify it worked:
```bash
python --version
```

### 2. Create a virtual environment

A virtual environment is an isolated folder where this project's Python
packages are installed, so they don't conflict with other projects on your
machine.

**Windows (PowerShell):**
```powershell
python -m venv venv
```

**macOS/Linux:**
```bash
python3 -m venv venv
```

### 3. Activate the virtual environment

You need to do this every time you open a new terminal to work on the project.

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```
> If PowerShell blocks this with an execution-policy error, run:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and try again.

**Windows (cmd.exe):**
```cmd
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

You'll know it worked because your terminal prompt now starts with `(venv)`.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Create your `.env` file

**Windows:**
```cmd
copy .env.example .env
```
**macOS/Linux:**
```bash
cp .env.example .env
```

### 6. Add your credentials

Open `.env` in any text editor and paste in the values you copied in Part 4.

### 7. Run the application

```bash
streamlit run app/streamlit_app.py
```
or
```bash
python cli.py list
```

---

## Part 8 — Understanding the Python Code

### `app/config.py`
**Purpose:** the ONLY file that reads environment variables. Every other
file imports the shared `settings` object from here instead of calling
`os.getenv()` directly. If a required variable is missing, this file raises
a clear error immediately (`_require()`) instead of letting the app crash
mysteriously later.

### `app/supabase_client.py`
**Purpose:** creates exactly ONE Supabase client object and reuses it
everywhere (`@lru_cache`), instead of reconnecting on every function call.
`create_client(url, service_role_key)` is the standard `supabase-py` call
that returns an object with `.table(...)` (database) and `.storage.from_(...)`
(storage) methods attached.

### `app/edge_function_client.py`
**Purpose:** the ONLY file that knows how to call our Edge Function. It
sends a plain HTTPS POST request (using the `requests` library) with a JSON
body of `{file_name, file_type, file_size, category}`, and parses the JSON
response into a `ValidationResult` object. If the network call fails or the
function is unreachable, it raises `EdgeFunctionError` so the caller can
show a friendly message instead of crashing.

### `app/document_service.py`
**Purpose:** this is where ALL Storage + Database + Edge Function
coordination happens — the "business logic" layer. Both the Streamlit UI
and the CLI call these same functions, so behavior can never diverge between
them. Key functions:

- `upload_document()` — the full CREATE flow: validate → upload to Storage →
  insert into Database, with automatic rollback if the Database insert fails
  after the Storage upload already succeeded.
- `list_documents()` / `get_document()` — READ operations using
  `client.table("documents").select("*")`.
- `download_document()` — READ, but for the file bytes:
  `client.storage.from_(bucket).download(path)`.
- `update_document_metadata()` — UPDATE, database-only (changes description/category).
- `replace_document_file()` — UPDATE, that also swaps the underlying file:
  uploads the new file FIRST, updates the database row to point at it, and
  only THEN deletes the old file — see Part 11 for why this order is chosen.
- `delete_document()` — DELETE, removing the database row first and then the
  Storage object — again, see Part 11 for why this specific order matters.

Every function that talks to Supabase is wrapped in a `try/except` that
catches the SDK's generic exceptions and re-raises a `DocumentServiceError`
with a **human-readable** message — this is what lets the Streamlit UI show
`st.error(str(exc))` directly instead of a scary Python traceback.

### `app/utils.py`
**Purpose:** small, pure formatting helpers (`format_file_size`,
`format_datetime`, `get_file_icon`) shared by both the UI and the CLI so
numbers and dates always look the same everywhere.

### `app/streamlit_app.py`
**Purpose:** UI ONLY. It never talks to Supabase directly — every button
click calls a function from `document_service.py`. It's organized as: theme
CSS → session state (tracks which page/modal is open) → sidebar navigation →
one render function per page (Dashboard/Documents/Upload/Settings) → a tiny
router at the bottom that calls the right render function.

### `cli.py`
**Purpose:** the terminal-only interface required by the internship task. It
uses Python's built-in `argparse` to turn commands like
`python cli.py upload file.pdf --category Finance` into calls to the exact
same `document_service.py` functions the UI uses.

---

## Part 9 — Edge Functions Explained from Zero

### What is an Edge Function?

It's a small program that Supabase runs for you on its own servers, triggered
by an HTTPS request. You write the code, run one deploy command, and
Supabase takes care of hosting, scaling, and running it close to wherever
the request came from ("the edge" of the network).

### Why is it called "serverless"?

Not because there's no server involved — obviously a computer somewhere runs
your code — but because **you** never provision, patch, or manage that
server. You don't pick an operating system, don't install a web server,
don't configure scaling. You just write a function; the infrastructure is
entirely Supabase's responsibility.

### What is Deno?

**Deno** is the JavaScript/TypeScript runtime that executes Supabase Edge
Functions (created by the original creator of Node.js, as a modern
redesign). Practically, for this project, the important facts are: it runs
TypeScript directly (no separate build step), and it supports standard Web
APIs like `Request`/`Response`/`fetch` — the same APIs your code would use
in a browser — instead of Node-specific APIs.

### Why TypeScript?

TypeScript is JavaScript with optional type annotations
(`file_size: number` instead of just `file_size`). It's the default and
best-supported language for Supabase Edge Functions, and the type
annotations help catch mistakes (like accidentally comparing a string to a
number) before the function is even deployed.

### Why use an Edge Function instead of just doing this in Python?

Our Python code is trusted backend code, so technically the validation logic
COULD live there instead. We use an Edge Function here because:

1. **The internship task requires demonstrating a real Edge Function.**
2. It's a genuinely reusable pattern: this same validation endpoint could be
   called by a future mobile app, a different frontend, or even tested
   directly with `curl` — without duplicating the validation rules in every
   client that needs them.
3. It demonstrates the "single source of truth for business rules, callable
   from anywhere" pattern that's common in real production systems.

### Why is server-side validation useful?

Any validation that happens ONLY in a browser or ONLY on the user's machine
can be bypassed — a user (or a bug) could send a request directly to your
database or storage, skipping the checks entirely. Running validation on a
server you control (whether that's a traditional backend or an Edge
Function) means the check is enforced no matter what client is talking to
your system.

### How the function receives data

`validate-document/index.ts` is a standard HTTP handler: `serve(async (req) => {...})`.
It reads the request body with `await req.json()`, expecting
`{ file_name, file_type, file_size, category }`.

### How it validates the document

It checks, in order:
1. Are `file_name`, `file_type`, `file_size` present and the right type?
2. Is the file extension on the allow-list (`ALLOWED_EXTENSIONS`)?
3. Is the MIME type on the allow-list (`ALLOWED_MIME_TYPES`)?
4. Is `file_size` under the 20 MB limit (`MAX_FILE_SIZE_BYTES`)?

### How it returns a response

- **Success:** HTTP 200 with `{ valid: true, data: { normalized_category, validation_tag, checked_at } }`
- **Validation failure:** HTTP 422 with `{ valid: false, errors: [...] }`
- **Malformed request:** HTTP 400 with `{ valid: false, errors: [...] }`

### Installing the Supabase CLI

You don't need a separate global install — `npx` (which ships with Node.js)
downloads and runs it on demand. Install Node.js from
[nodejs.org](https://nodejs.org) first if you don't have it.

### The deployment commands, explained

```bash
npx supabase login
```
Opens a browser window to authenticate the CLI with your Supabase account,
so it's allowed to deploy functions on your behalf.

```bash
npx supabase init
```
Creates a local `supabase/` config folder (this project already has one)
that tracks your project's functions and settings.

```bash
npx supabase link --project-ref <your-project-ref>
```
Connects your local folder to your actual Supabase project in the cloud.
Find `<your-project-ref>` in your Project URL —
`https://<project-ref>.supabase.co`.

```bash
npx supabase functions new validate-document
```
Scaffolds a new function folder — **not needed here**, since this repo
already includes `supabase/functions/validate-document/index.ts`. Only run
this if you're creating a brand-new function from scratch.

```bash
npx supabase functions deploy validate-document
```
Uploads and deploys the function code to Supabase's servers, making it live
at `https://<project-ref>.supabase.co/functions/v1/validate-document`.

### Testing locally (before deploying)

```bash
npx supabase functions serve validate-document
```
Runs the function on your own machine at `http://localhost:54321/functions/v1/validate-document`
so you can test changes instantly without deploying. Requires Docker Desktop
to be installed and running (Supabase's local dev environment uses Docker
under the hood).

### Finding the deployed function

In your dashboard, click **Edge Functions** in the sidebar — you'll see
`validate-document` listed with its status and invocation logs, useful for
debugging if something goes wrong.

### How Python calls it

`app/edge_function_client.py` sends a plain HTTPS POST request to
`{SUPABASE_URL}/functions/v1/validate-document` using the `requests`
library — no special SDK needed, since an Edge Function is just a normal web
endpoint.

---

## Part 10 — Complete End-to-End Flow

```text
User selects file
        ↓
Frontend (Streamlit or CLI) reads the file into memory
        ↓
Python application (document_service.upload_document)
        ↓
Validate basic input (file not empty, under size limit)
        ↓
Call Edge Function (validate-document) with name/type/size
        ↓
Edge Function validates extension, MIME type, and size
        ↓
Python receives the validation response
        ↓
   ┌─── If INVALID: stop here, show the error message to the user
   │
   └─── If VALID: continue ↓
        ↓
Upload file bytes to Supabase Storage (unique generated path)
        ↓
Insert metadata row into PostgreSQL (including storage_path)
        ↓
   ┌─── If the insert FAILS: delete the just-uploaded file from
   │    Storage (rollback), show the error to the user
   │
   └─── If the insert SUCCEEDS: continue ↓
        ↓
UI refreshes its document list
        ↓
Document appears in the dashboard / documents page
```

### What happens when something fails

- **Edge Function unreachable/times out** → `EdgeFunctionError` is raised,
  caught in `upload_document()`, re-raised as a friendly
  `DocumentServiceError` — no file is ever uploaded to Storage.
- **Edge Function says invalid** → same friendly error path, again nothing
  is uploaded.
- **Storage upload fails** (e.g. bucket doesn't exist) → friendly error,
  nothing is written to the database.
- **Database insert fails** (e.g. constraint violation) **after** Storage
  upload succeeded → the code automatically deletes the orphaned file from
  Storage before showing the error, so Storage and Database never drift out
  of sync.

---

## Part 11 — CRUD Explained in Detail

### CREATE

1. Client-side check: is the file empty? Over the configured size limit?
2. **Edge Function** validates type/size server-side and returns a
   normalized category + validation tag.
3. **Storage operation**: `client.storage.from_(bucket).upload(...)` writes
   the raw bytes to a freshly generated, collision-proof path.
4. **Database operation**: `client.table("documents").insert(...)` writes
   the metadata row, including the `storage_path` from step 3.
5. If step 4 fails, step 3's upload is rolled back (deleted).

### READ

- **Metadata retrieval**: `client.table("documents").select("*")`, optionally
  filtered by category and ordered by `uploaded_at`.
- **File download**: `client.storage.from_(bucket).download(storage_path)`
  returns the raw bytes, which the UI then offers via `st.download_button`
  or the CLI writes straight to disk.
- We also offer **signed URLs** (`get_public_url()`) — temporary links
  (expire in 1 hour) for viewing a file directly, useful since the bucket is
  private.

### UPDATE

Two distinct update paths:

1. **Metadata-only update** (`update_document_metadata`) — a plain
   `client.table("documents").update({...}).eq("id", ...)` call. No Storage
   interaction at all.
2. **File replacement** (`replace_document_file`) — more delicate, because
   TWO systems need to stay in sync:
   - Upload the NEW file to a NEW storage path first.
   - Update the database row to point at the new path (and new size/type).
   - Only THEN delete the OLD file from Storage.

   **Why this order?** If we deleted the old file first and the new upload
   then failed, the document row would point at nothing — a broken,
   unrecoverable state for the user. Uploading first means the worst case if
   something fails partway is a harmless leftover file in Storage, not a
   broken document.

### DELETE

`delete_document()` removes the database row **first**, then the Storage
object:

- **Database deletion**: `client.table("documents").delete().eq("id", ...)`
- **Storage deletion**: `client.storage.from_(bucket).remove([storage_path])`

**What happens if one succeeds and the other fails?** We deliberately delete
the database row first. If the subsequent Storage deletion then fails, the
result is an **orphaned file** sitting in Storage with no database row
pointing at it — invisible to the app and harmless, just wasted storage
space that can be cleaned up later. The alternative order (Storage first)
is worse: if the database deletion then failed, the UI would show a document
whose "Download" button is permanently broken, actively confusing the user.
We chose the failure mode that keeps the user-facing experience consistent.

---

## Part 12 — Troubleshooting

| Problem | Why it happens | How to fix it |
|---|---|---|
| **Invalid API key** | Wrong key copied, extra whitespace, or using the anon key where the service_role key is required | Re-copy the key from Project Settings → API, check for trailing spaces, confirm `.env` uses `SUPABASE_SERVICE_ROLE_KEY` |
| **Wrong Supabase URL** | Typo, or copied a different project's URL | Re-copy exactly from Project Settings → API → Project URL |
| **Bucket does not exist** | `STORAGE_BUCKET` in `.env` doesn't match the bucket name created in the dashboard | Check Storage in the dashboard, ensure names match exactly (case-sensitive) |
| **Permission denied on Storage/DB** | Using the anon key instead of service_role, or RLS policy missing | Confirm `.env` has a valid `SUPABASE_SERVICE_ROLE_KEY`; re-run `database/schema.sql` to ensure the RLS policy exists |
| **Storage upload failed** | Bucket missing, network issue, or file bytes empty | Verify the bucket exists and is named correctly; check your internet connection |
| **Database insert failed** | A `not null` or `check` constraint was violated, or `storage_path` collided | Read the technical detail in the error message — it names the exact constraint |
| **Edge Function not found (404)** | Function not deployed yet, or `EDGE_FUNCTION_NAME` typo | Run `npx supabase functions deploy validate-document`; check the name matches exactly |
| **Edge Function deployment failed** | Not logged in, not linked to the project, or a TypeScript syntax error | Run `npx supabase login` then `npx supabase link --project-ref <ref>` again; check the CLI's error output for syntax issues |
| **`supabase` command not recognized** | Node/npx not installed, or trying to run `supabase` directly instead of via `npx` | Install Node.js from nodejs.org; always prefix commands with `npx` unless you've installed the CLI globally |
| **Python package missing (ModuleNotFoundError)** | Virtual environment not activated, or `pip install -r requirements.txt` never run | Activate `venv` (see Part 7), then re-run `pip install -r requirements.txt` |
| **`.env` not loading / "Missing required environment variable"** | `.env` file doesn't exist yet, is misnamed (e.g. `.env.txt`), or is in the wrong directory | Copy `.env.example` to exactly `.env` in the project root; confirm you're running commands from the project root |
| **CORS problems** | Only relevant if calling the Edge Function from a browser-based frontend directly | The function already sends permissive CORS headers; if building a different frontend, ensure you're not blocked by browser dev tools' console — check the Network tab for the actual error |
| **File type validation keeps rejecting a file that should be allowed** | Extension or MIME type isn't in the Edge Function's allow-list | Add the extension to `ALLOWED_EXTENSIONS` and the MIME type to `ALLOWED_MIME_TYPES` in `supabase/functions/validate-document/index.ts`, then redeploy |
| **Service role key problems (works locally, fails when deployed elsewhere)** | Key not set in the new environment's secrets/environment variables | Set all `.env` variables again in whatever hosting platform you deploy to (they are never read from `.env` automatically outside your local machine) |
| **RLS problems ("new row violates row-level security policy")** | The RLS policy from `schema.sql` wasn't applied, or you're using the anon key | Re-run `database/schema.sql`; confirm the app uses the service_role key |
| **Storage policies problems** | Private bucket + trying to access a file without the service_role key or a valid signed URL | Use the service_role key server-side (already default in this project), or generate a signed URL via `get_public_url()` |

---

## Part 13 — Concepts to Understand Before Presenting

A quick-reference cheat sheet, in simple English, with examples from this
exact project:

1. **Supabase** — a managed backend platform giving us a database, file
   storage, and serverless functions in one place. We use it so we don't
   have to build/host our own server.
2. **PostgreSQL** — the actual database engine Supabase uses. Our `documents`
   table lives here.
3. **Supabase Storage** — the file storage system where the real PDF/image
   bytes live, separate from the database.
4. **Storage bucket** — a named container inside Storage (`documents`),
   similar to a folder, that groups our uploaded files.
5. **Edge Function** — our `validate-document` function: small server-side
   code that checks a file is allowed before we save anything.
6. **Deno** — the runtime that executes our Edge Function's TypeScript code.
7. **CRUD** — Create, Read, Update, Delete: the four basic operations every
   part of this app performs on both files (Storage) and metadata
   (Database).
8. **How Python connects to Supabase** — via `supabase-py`, a client library
   that turns Python function calls (`client.table(...)`) into HTTPS
   requests to Supabase's auto-generated API.
9. **How files are stored** — as raw bytes in the `documents` Storage
   bucket, under a generated path like `2026/08/9f3a1c2b_invoice.pdf`.
10. **How metadata is stored** — as a row in the `documents` PostgreSQL
    table, with a `storage_path` column linking it to the actual file.
11. **Why we need both Storage and Database** — Storage is efficient for
    large file bytes; the Database is efficient for searchable, structured
    data. Neither is good at the other's job.
12. **How the Edge Function fits in** — it's called once, mid-upload,
    between "user picked a file" and "we save anything," acting as a
    server-side gatekeeper.
13. **API keys** — credentials that authenticate our app to Supabase; the
    anon key is safe for browsers, the service_role key is a full-access
    secret for server-side code only.
14. **RLS (Row Level Security)** — Postgres's per-row permission system;
    blocks all access by default until you add a policy explaining who can
    do what.
15. **Storage policies** — the Storage equivalent of RLS, controlling who
    can upload/download/delete files in a bucket.
16. **What happens during upload** — validate (Edge Function) → upload
    (Storage) → insert (Database), with rollback if the last step fails.
17. **What happens during update** — either a metadata-only database update,
    or a full file replacement that uploads new-then-deletes-old to avoid
    ever leaving a broken document.
18. **What happens during delete** — the database row is removed first, then
    the Storage file, chosen specifically so a partial failure never leaves
    a broken "download" button visible to the user.

---

You now know everything this project uses. Good luck presenting it! 🎉
