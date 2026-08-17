"""
supabase_client.py
===================
Creates and caches ONE Supabase client for the whole app to reuse.

WHY THE SERVICE ROLE KEY?
--------------------------
Supabase gives you two API keys:

  - ANON key   -> meant for browser/mobile apps. It is SAFE to expose
                  publicly because Row Level Security (RLS) policies
                  restrict what it can do.
  - SERVICE ROLE key -> a master key that BYPASSES RLS entirely. It
                  must NEVER be shipped to a browser or mobile app.

This project's Python code runs entirely on the server (or on your own
machine, acting as the "backend"), never inside a user's browser, so it
is an appropriate place to use the service role key. This lets our
single-user internship app perform Storage/Database operations without
needing to build a full authentication system, while keeping the key
out of any client-side code. See SUPABASE_GUIDE.md Part 4 for the full
explanation and the security trade-offs.
"""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Returns a cached Supabase client authenticated with the service
    role key. Cached with lru_cache so we only create one client
    instance per process instead of reconnecting on every function call.
    """
    if not settings.supabase_service_role_key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY is not set. This app needs it to "
            "read/write Storage and the database from the server side. "
            "Add it to your .env file (see .env.example)."
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
