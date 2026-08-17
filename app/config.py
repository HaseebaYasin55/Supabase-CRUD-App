"""
config.py
=========
Loads Supabase credentials and app settings from environment variables
(read from a local .env file via python-dotenv).

WHY A SEPARATE CONFIG FILE?
----------------------------
Keeping all environment/configuration reading in ONE place means:
  - No other file ever hardcodes a credential.
  - If a required variable is missing, the app fails fast with a clear
    error message instead of a confusing crash somewhere deep in the code.
  - Every other module just does `from app.config import settings`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load variables from a `.env` file (if present) into the process
# environment. This does nothing in production environments where
# real environment variables are already set (e.g. Streamlit Cloud
# secrets, Docker env, etc.) — it only fills gaps for local dev.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    storage_bucket: str
    edge_function_name: str
    max_file_size_mb: int

    @property
    def edge_function_url(self) -> str:
        """Builds the full HTTPS URL of our deployed Edge Function."""
        return f"{self.supabase_url}/functions/v1/{self.edge_function_name}"


def _require(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable '{var_name}'. "
            f"Copy .env.example to .env and fill in your Supabase credentials. "
            f"See SUPABASE_GUIDE.md Part 4 for where to find these values."
        )
    return value


def load_settings() -> Settings:
    return Settings(
        supabase_url=_require("SUPABASE_URL"),
        supabase_anon_key=_require("SUPABASE_ANON_KEY"),
        # Service role key is optional at import time so the app can still
        # show a helpful error inside the UI rather than crashing on import.
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        storage_bucket=os.getenv("STORAGE_BUCKET", "documents"),
        edge_function_name=os.getenv("EDGE_FUNCTION_NAME", "validate-document"),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "20")),
    )


# A single shared settings instance other modules import.
settings = load_settings()
