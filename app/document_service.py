"""
document_service.py
=====================
This is the HEART of the application. Every CRUD operation the UI and
the CLI perform goes through the functions in this file. Keeping all
Storage + Database + Edge Function coordination in ONE place means:

  - The Streamlit UI and the CLI both call the exact same functions,
    so behavior never diverges between them.
  - Storage/Database consistency logic (see `delete_document`) lives
    in exactly one spot instead of being duplicated.

TABLE:   public.documents   (see database/schema.sql)
BUCKET:  "documents"        (see SUPABASE_GUIDE.md Part 6)
"""

from __future__ import annotations

import logging
import mimetypes
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.edge_function_client import EdgeFunctionError, validate_document
from app.supabase_client import get_supabase_client

logger = logging.getLogger("document_service")
logging.basicConfig(level=logging.INFO)

TABLE_NAME = "documents"


class DocumentServiceError(Exception):
    """A friendly, UI-safe error. Callers should show `str(exc)` directly."""


@dataclass
class Document:
    id: str
    file_name: str
    storage_path: str
    file_type: str
    file_size: int
    description: str | None
    category: str
    validation_tag: str | None
    uploaded_at: str
    updated_at: str

    @staticmethod
    def from_row(row: dict) -> "Document":
        return Document(
            id=row["id"],
            file_name=row["file_name"],
            storage_path=row["storage_path"],
            file_type=row["file_type"],
            file_size=row["file_size"],
            description=row.get("description"),
            category=row.get("category", "General"),
            validation_tag=row.get("validation_tag"),
            uploaded_at=row["uploaded_at"],
            updated_at=row["updated_at"],
        )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _guess_mime_type(file_name: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_name)
    return mime_type or "application/octet-stream"


def _build_storage_path(file_name: str) -> str:
    """
    Builds a unique storage path so two different uploads of a file
    named "invoice.pdf" never collide inside the bucket. We namespace
    by year/month for tidiness and prefix with a short UUID.

    Example: 2026/08/9f3a1c2b_invoice.pdf
    """
    safe_name = file_name.replace(" ", "_")
    today = datetime.now(timezone.utc)
    unique_prefix = uuid.uuid4().hex[:8]
    return f"{today:%Y}/{today:%m}/{unique_prefix}_{safe_name}"


# ---------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------

def upload_document(
    file_bytes: bytes,
    file_name: str,
    description: str = "",
    category: str = "General",
) -> Document:
    """
    Full CREATE flow:
      1. Basic client-side sanity checks (empty file).
      2. Call the Edge Function to validate type/size server-side and
         get back a normalized category + validation tag.
      3. Upload the raw bytes to Supabase Storage.
      4. Insert the metadata row into PostgreSQL.

    If step 4 fails after step 3 succeeded, we roll back the Storage
    upload so we never leave an "orphan" file with no matching row.
    """
    if not file_bytes:
        raise DocumentServiceError("The selected file is empty.")

    file_size = len(file_bytes)
    file_type = _guess_mime_type(file_name)

    if file_size > settings.max_file_size_mb * 1024 * 1024:
        raise DocumentServiceError(
            f"File is too large ({file_size / (1024*1024):.2f} MB). "
            f"Max allowed is {settings.max_file_size_mb} MB."
        )

    # --- Step 1: server-side validation via Edge Function -----------
    try:
        result = validate_document(file_name, file_type, file_size, category)
    except EdgeFunctionError as exc:
        logger.error("Edge Function call failed: %s", exc)
        raise DocumentServiceError(
            "Could not validate the document because the validation service "
            "is unreachable. Please check that the Edge Function is deployed "
            "and try again."
        ) from exc

    if not result.valid:
        raise DocumentServiceError("Validation failed: " + "; ".join(result.errors or []))

    normalized_category = result.normalized_category or category
    validation_tag = result.validation_tag

    # --- Step 2: upload bytes to Storage -----------------------------
    storage_path = _build_storage_path(file_name)
    client = get_supabase_client()

    try:
        client.storage.from_(settings.storage_bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file_type},
        )
    except Exception as exc:  # supabase-py raises generic StorageException
        logger.error("Storage upload failed: %s", exc)
        raise DocumentServiceError(
            f"Failed to upload '{file_name}' to Storage. "
            f"Make sure the '{settings.storage_bucket}' bucket exists. "
            f"Technical detail: {exc}"
        ) from exc

    # --- Step 3: insert metadata row into PostgreSQL -----------------
    try:
        response = (
            client.table(TABLE_NAME)
            .insert(
                {
                    "file_name": file_name,
                    "storage_path": storage_path,
                    "file_type": file_type,
                    "file_size": file_size,
                    "description": description or None,
                    "category": normalized_category,
                    "validation_tag": validation_tag,
                }
            )
            .execute()
        )
    except Exception as exc:
        logger.error("Database insert failed after Storage upload succeeded: %s", exc)
        # Roll back the orphaned Storage object so Storage and DB stay in sync.
        try:
            client.storage.from_(settings.storage_bucket).remove([storage_path])
        except Exception as rollback_exc:
            logger.error("Rollback also failed — orphan file left in Storage: %s", rollback_exc)
        raise DocumentServiceError(
            f"Failed to save document metadata to the database. "
            f"The uploaded file was rolled back. Technical detail: {exc}"
        ) from exc

    row = response.data[0] if response.data else None

   # Some Supabase/PostgREST setups don't send back the full row after an
   # insert. If that happens, fetch the row we just created using its
   # unique storage_path instead of crashing.
    if not row or "id" not in row:
       fetch_response = (
           client.table(TABLE_NAME)
           .select("*")
           .eq("storage_path", storage_path)
           .single()
           .execute()
       )
       row = fetch_response.data

    logger.info("Uploaded document '%s' (id=%s)", file_name, row["id"])
    return Document.from_row(row)


# ---------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------

def list_documents(category: str | None = None) -> list[Document]:
    """Returns all documents, most recently uploaded first."""
    client = get_supabase_client()
    try:
        query = client.table(TABLE_NAME).select("*").order("uploaded_at", desc=True)
        if category and category != "All":
            query = query.eq("category", category)
        response = query.execute()
    except Exception as exc:
        logger.error("Database read failed: %s", exc)
        raise DocumentServiceError(f"Failed to load documents from the database: {exc}") from exc

    return [Document.from_row(row) for row in response.data]


def get_document(document_id: str) -> Document:
    client = get_supabase_client()
    try:
        response = client.table(TABLE_NAME).select("*").eq("id", document_id).single().execute()
    except Exception as exc:
        raise DocumentServiceError(f"Document not found or database read failed: {exc}") from exc
    return Document.from_row(response.data)


def download_document(document: Document) -> bytes:
    """Downloads the raw file bytes from Storage for a given document row."""
    client = get_supabase_client()
    try:
        return client.storage.from_(settings.storage_bucket).download(document.storage_path)
    except Exception as exc:
        logger.error("Storage download failed for %s: %s", document.storage_path, exc)
        raise DocumentServiceError(
            f"Failed to download '{document.file_name}' from Storage. "
            f"The file may have been removed directly from the bucket. Technical detail: {exc}"
        ) from exc


def get_public_url(document: Document) -> str | None:
    """
    Returns a signed, temporary URL for viewing/downloading the file
    directly (useful for "Open in browser" links). Returns None if the
    bucket is private and generating a signed URL fails.
    """
    client = get_supabase_client()
    try:
        result = client.storage.from_(settings.storage_bucket).create_signed_url(
            document.storage_path, expires_in=3600
        )
        return result.get("signedURL") or result.get("signed_url")
    except Exception as exc:
        logger.warning("Could not create signed URL: %s", exc)
        return None


# ---------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------

def update_document_metadata(
    document_id: str,
    description: str | None = None,
    category: str | None = None,
) -> Document:
    """Updates only metadata fields (no file replacement)."""
    client = get_supabase_client()
    updates: dict = {}
    if description is not None:
        updates["description"] = description
    if category is not None:
        updates["category"] = category

    if not updates:
        raise DocumentServiceError("Nothing to update — provide a new description or category.")

    try:
        response = client.table(TABLE_NAME).update(updates).eq("id", document_id).execute()
    except Exception as exc:
        logger.error("Database update failed: %s", exc)
        raise DocumentServiceError(f"Failed to update document metadata: {exc}") from exc

    if not response.data:
        raise DocumentServiceError("Document not found.")

    return Document.from_row(response.data[0])


def replace_document_file(document_id: str, new_file_bytes: bytes, new_file_name: str) -> Document:
    """
    Replaces the underlying file for an existing document row:
      1. Validate the new file via the Edge Function.
      2. Upload the new file to a NEW storage path.
      3. Update the row to point at the new path + new size/type.
      4. Delete the OLD file from Storage.

    We upload-then-delete (rather than delete-then-upload) so that if
    the new upload fails, the old file is still safely in Storage and
    the database row still points at valid data — Storage and Database
    are never left inconsistent.
    """
    if not new_file_bytes:
        raise DocumentServiceError("The selected replacement file is empty.")

    client = get_supabase_client()
    existing = get_document(document_id)

    new_file_size = len(new_file_bytes)
    new_file_type = _guess_mime_type(new_file_name)

    try:
        result = validate_document(new_file_name, new_file_type, new_file_size, existing.category)
    except EdgeFunctionError as exc:
        raise DocumentServiceError(f"Could not validate the replacement file: {exc}") from exc
    if not result.valid:
        raise DocumentServiceError("Validation failed: " + "; ".join(result.errors or []))

    new_storage_path = _build_storage_path(new_file_name)

    try:
        client.storage.from_(settings.storage_bucket).upload(
            path=new_storage_path,
            file=new_file_bytes,
            file_options={"content-type": new_file_type},
        )
    except Exception as exc:
        raise DocumentServiceError(f"Failed to upload the replacement file: {exc}") from exc

    try:
        response = (
            client.table(TABLE_NAME)
            .update(
                {
                    "file_name": new_file_name,
                    "storage_path": new_storage_path,
                    "file_type": new_file_type,
                    "file_size": new_file_size,
                    "validation_tag": result.validation_tag,
                }
            )
            .eq("id", document_id)
            .execute()
        )
    except Exception as exc:
        logger.error("Database update failed after new file uploaded — rolling back new file: %s", exc)
        try:
            client.storage.from_(settings.storage_bucket).remove([new_storage_path])
        except Exception as rollback_exc:
            logger.error("Rollback of new file also failed: %s", rollback_exc)
        raise DocumentServiceError(f"Failed to update document record: {exc}") from exc

    # Only now, after the DB successfully points at the new file, remove the old one.
    try:
        client.storage.from_(settings.storage_bucket).remove([existing.storage_path])
    except Exception as exc:
        logger.warning(
            "New file replaced successfully but old file '%s' could not be deleted "
            "(orphan left in Storage): %s",
            existing.storage_path,
            exc,
        )

    return Document.from_row(response.data[0])


# ---------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------

def delete_document(document_id: str) -> None:
    """
    Deletes both the Storage object and the database row.

    ORDER MATTERS: we delete the database row FIRST. If Storage
    deletion then fails, we're left with an orphaned file with NO
    metadata pointing at it — annoying, but harmless and cleanable
    later. The reverse order (delete Storage first, DB second) is
    worse: if the DB delete then failed, the UI would show a document
    row whose "Download" button is permanently broken. We choose the
    failure mode that leaves the user-facing experience consistent.
    """
    client = get_supabase_client()
    existing = get_document(document_id)

    try:
        client.table(TABLE_NAME).delete().eq("id", document_id).execute()
    except Exception as exc:
        logger.error("Database delete failed: %s", exc)
        raise DocumentServiceError(f"Failed to delete document record: {exc}") from exc

    try:
        client.storage.from_(settings.storage_bucket).remove([existing.storage_path])
    except Exception as exc:
        logger.warning(
            "Document record deleted but the file in Storage ('%s') could not be "
            "removed. It is now an orphaned file with no metadata: %s",
            existing.storage_path,
            exc,
        )
