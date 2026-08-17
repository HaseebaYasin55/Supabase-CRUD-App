"""
utils.py
=========
Small, dependency-free formatting helpers shared by the Streamlit UI
and the CLI, so both display sizes/dates identically.
"""

from __future__ import annotations

from datetime import datetime


def format_file_size(num_bytes: int) -> str:
    """Converts a byte count into a human-readable string, e.g. '1.4 MB'."""
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_datetime(iso_string: str) -> str:
    """Converts an ISO timestamp from Supabase into 'Aug 17, 2026 09:30 AM'."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %I:%M %p")
    except (ValueError, AttributeError):
        return iso_string


FILE_ICONS = {
    "pdf": "📄",
    "png": "🖼️",
    "jpg": "🖼️",
    "jpeg": "🖼️",
    "webp": "🖼️",
    "txt": "📝",
    "csv": "📊",
    "doc": "📃",
    "docx": "📃",
    "xls": "📊",
    "xlsx": "📊",
    "zip": "🗜️",
    "json": "🧩",
}


def get_file_icon(file_name: str) -> str:
    ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
    return FILE_ICONS.get(ext, "📁")
