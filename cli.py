"""
cli.py
=======
Terminal-based CRUD tool. This satisfies the internship requirement to
demonstrate the core CRUD functionality WITHOUT any UI, using nothing
but the command line. It reuses the exact same `app/document_service.py`
functions the Streamlit UI uses, so we're never duplicating logic.

USAGE
-----
    python cli.py upload <path> [--description TEXT] [--category TEXT]
    python cli.py list [--category TEXT]
    python cli.py show <document_id>
    python cli.py download <document_id> [--out PATH]
    python cli.py update <document_id> [--description TEXT] [--category TEXT]
    python cli.py replace <document_id> <new_file_path>
    python cli.py delete <document_id> [--yes]

EXAMPLES
--------
    python cli.py upload ./sample.pdf --description "Q3 report" --category Finance
    python cli.py list
    python cli.py list --category Finance
    python cli.py show 3fa85f64-5717-4562-b3fc-2c963f66afa6
    python cli.py download 3fa85f64-5717-4562-b3fc-2c963f66afa6 --out ./downloaded.pdf
    python cli.py update 3fa85f64-... --description "Updated Q3 report"
    python cli.py replace 3fa85f64-... ./new_version.pdf
    python cli.py delete 3fa85f64-... --yes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.document_service import (
    DocumentServiceError,
    delete_document,
    download_document,
    get_document,
    list_documents,
    replace_document_file,
    update_document_metadata,
    upload_document,
)
from app.utils import format_datetime, format_file_size, get_file_icon


def cmd_upload(args: argparse.Namespace) -> None:
    path = Path(args.path)
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    file_bytes = path.read_bytes()
    print(f"Uploading '{path.name}' ({format_file_size(len(file_bytes))})...")
    try:
        doc = upload_document(
            file_bytes=file_bytes,
            file_name=path.name,
            description=args.description or "",
            category=args.category or "General",
        )
    except DocumentServiceError as exc:
        print(f"❌ Upload failed: {exc}")
        sys.exit(1)

    print("✅ Upload successful!")
    print(f"   id:              {doc.id}")
    print(f"   file_name:       {doc.file_name}")
    print(f"   category:        {doc.category}")
    print(f"   validation_tag:  {doc.validation_tag}")
    print(f"   storage_path:    {doc.storage_path}")


def cmd_list(args: argparse.Namespace) -> None:
    try:
        docs = list_documents(category=args.category)
    except DocumentServiceError as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    if not docs:
        print("No documents found. Upload one with: python cli.py upload <path>")
        return

    print(f"{'ICON':<4} {'NAME':<30} {'CATEGORY':<15} {'SIZE':<10} {'UPLOADED':<20} {'ID'}")
    print("-" * 110)
    for doc in docs:
        icon = get_file_icon(doc.file_name)
        print(
            f"{icon:<4} {doc.file_name[:29]:<30} {doc.category[:14]:<15} "
            f"{format_file_size(doc.file_size):<10} {format_datetime(doc.uploaded_at):<20} {doc.id}"
        )
    print(f"\nTotal: {len(docs)} document(s)")


def cmd_show(args: argparse.Namespace) -> None:
    try:
        doc = get_document(args.document_id)
    except DocumentServiceError as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    print(f"id:              {doc.id}")
    print(f"file_name:       {doc.file_name}")
    print(f"file_type:       {doc.file_type}")
    print(f"file_size:       {format_file_size(doc.file_size)}")
    print(f"category:        {doc.category}")
    print(f"description:     {doc.description or '(none)'}")
    print(f"storage_path:    {doc.storage_path}")
    print(f"validation_tag:  {doc.validation_tag}")
    print(f"uploaded_at:     {format_datetime(doc.uploaded_at)}")
    print(f"updated_at:      {format_datetime(doc.updated_at)}")


def cmd_download(args: argparse.Namespace) -> None:
    try:
        doc = get_document(args.document_id)
        file_bytes = download_document(doc)
    except DocumentServiceError as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    out_path = Path(args.out) if args.out else Path(doc.file_name)
    out_path.write_bytes(file_bytes)
    print(f"✅ Downloaded '{doc.file_name}' -> {out_path} ({format_file_size(len(file_bytes))})")


def cmd_update(args: argparse.Namespace) -> None:
    try:
        doc = update_document_metadata(
            args.document_id, description=args.description, category=args.category
        )
    except DocumentServiceError as exc:
        print(f"❌ Update failed: {exc}")
        sys.exit(1)
    print(f"✅ Updated document {doc.id}")
    print(f"   description: {doc.description or '(none)'}")
    print(f"   category:    {doc.category}")


def cmd_replace(args: argparse.Namespace) -> None:
    path = Path(args.new_file_path)
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    try:
        doc = replace_document_file(args.document_id, path.read_bytes(), path.name)
    except DocumentServiceError as exc:
        print(f"❌ Replace failed: {exc}")
        sys.exit(1)

    print(f"✅ File replaced for document {doc.id}")
    print(f"   new file_name: {doc.file_name}")
    print(f"   new size:      {format_file_size(doc.file_size)}")


def cmd_delete(args: argparse.Namespace) -> None:
    if not args.yes:
        confirm = input(f"Delete document {args.document_id}? This cannot be undone. [y/N] ")
        if confirm.strip().lower() != "y":
            print("Cancelled.")
            return
    try:
        delete_document(args.document_id)
    except DocumentServiceError as exc:
        print(f"❌ Delete failed: {exc}")
        sys.exit(1)
    print(f"✅ Deleted document {args.document_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Terminal CRUD tool for the Supabase Document Manager."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_upload = sub.add_parser("upload", help="Upload a new document")
    p_upload.add_argument("path", help="Path to the local file to upload")
    p_upload.add_argument("--description", help="Optional description")
    p_upload.add_argument("--category", help="Optional category (default: General)")
    p_upload.set_defaults(func=cmd_upload)

    p_list = sub.add_parser("list", help="List all documents")
    p_list.add_argument("--category", help="Filter by category")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show full metadata for one document")
    p_show.add_argument("document_id")
    p_show.set_defaults(func=cmd_show)

    p_download = sub.add_parser("download", help="Download a document's file")
    p_download.add_argument("document_id")
    p_download.add_argument("--out", help="Output file path (default: original file name)")
    p_download.set_defaults(func=cmd_download)

    p_update = sub.add_parser("update", help="Update a document's metadata")
    p_update.add_argument("document_id")
    p_update.add_argument("--description", help="New description")
    p_update.add_argument("--category", help="New category")
    p_update.set_defaults(func=cmd_update)

    p_replace = sub.add_parser("replace", help="Replace a document's underlying file")
    p_replace.add_argument("document_id")
    p_replace.add_argument("new_file_path")
    p_replace.set_defaults(func=cmd_replace)

    p_delete = sub.add_parser("delete", help="Delete a document (Storage + Database)")
    p_delete.add_argument("document_id")
    p_delete.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    p_delete.set_defaults(func=cmd_delete)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)
