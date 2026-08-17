# Manual Testing Checklist

This project relies on manual testing against a real Supabase project rather
than mocked automated tests, since Storage/Database/Edge Function behavior is
most meaningfully verified end-to-end. Work through this checklist after
completing setup (README.md → "Supabase Setup") to confirm every feature
works.

You can run each test through **either** the Streamlit UI or the CLI —
try both at least once to confirm they behave identically (they share the
same `document_service.py` code).

## Setup verification

- [ ] `database/schema.sql` ran successfully; `documents` table visible in Table Editor
- [ ] `documents` Storage bucket exists (private)
- [ ] `validate-document` Edge Function deployed and visible under Edge Functions
- [ ] `.env` filled in with real credentials
- [ ] `streamlit run app/streamlit_app.py` launches without errors
- [ ] `python cli.py list` runs without errors (should print "No documents found" on a fresh project)

## Create (Upload)

- [ ] Upload a valid PDF with a description and category → succeeds, appears in Documents page and Dashboard
- [ ] Upload a valid PNG/JPG image → succeeds
- [ ] Upload without a description (optional field) → succeeds, description shown as empty
- [ ] Upload a file with a **disallowed extension** (e.g. `.exe`) → rejected with a clear error, nothing appears in Storage or the database
- [ ] Upload a file **larger than MAX_FILE_SIZE_MB** → rejected with a clear error before any upload happens
- [ ] Upload with the Edge Function intentionally undeployed/misconfigured → app shows a friendly "Edge Function unreachable" error, not a raw traceback
- [ ] CLI: `python cli.py upload ./sample.pdf --description "Test" --category Finance` → succeeds and prints the new document's id

## Read (List / View / Download)

- [ ] Documents page lists all uploaded documents, most recent first
- [ ] Dashboard "Total Documents" and "Total Storage Used" numbers match reality
- [ ] Category filter narrows the list correctly
- [ ] Search by file name narrows the list correctly
- [ ] Download button retrieves the exact original file (compare file size/checksum to the original)
- [ ] CLI: `python cli.py list` shows all documents in a table
- [ ] CLI: `python cli.py show <id>` prints full metadata for one document
- [ ] CLI: `python cli.py download <id> --out ./test_download.pdf` produces an identical file

## Update

- [ ] Edit a document's description only → saved, file itself untouched
- [ ] Edit a document's category only → saved, reflected in the category filter
- [ ] Replace a document's file with a different file → new file downloadable, old file no longer accessible via the app, size/type updated in the UI
- [ ] Replace with an invalid file type → rejected, original file/record untouched
- [ ] CLI: `python cli.py update <id> --description "New text"` → succeeds
- [ ] CLI: `python cli.py replace <id> ./new_version.pdf` → succeeds, `show` reflects new file_name/size

## Delete

- [ ] Delete button shows a confirmation dialog before doing anything
- [ ] Canceling the confirmation does nothing
- [ ] Confirming deletes the document from both the list and (verify in Supabase dashboard) the Storage bucket and the `documents` table
- [ ] CLI: `python cli.py delete <id>` prompts for confirmation; `python cli.py delete <id> --yes` skips it

## Error handling / edge cases

- [ ] Empty document list shows the empty state with an "Upload Document" call to action
- [ ] Uploading with a stopped/incorrect `SUPABASE_URL` shows a friendly connection error, not a crash
- [ ] Attempting to view/download a document whose file was manually deleted from the Storage bucket (outside the app) shows a friendly "failed to download" error
- [ ] All error messages shown in the UI are plain English, not raw Python exceptions or stack traces

## Database CRUD (direct verification)

- [ ] After an upload, the row is visible in Supabase Table Editor with all expected columns filled in
- [ ] `updated_at` changes automatically after any metadata update (verify the trigger works)
- [ ] Deleting a row via the app removes it from Table Editor

## Storage CRUD (direct verification)

- [ ] After an upload, the file is visible in Supabase Storage browser at the expected path
- [ ] After a file replacement, the old path is gone and a new path exists
- [ ] After a delete, the file is gone from Storage
