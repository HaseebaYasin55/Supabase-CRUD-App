"""
edge_function_client.py
========================
Small wrapper responsible for ONE thing: calling our deployed
`validate-document` Edge Function over HTTPS and turning its JSON
response into a Python object our services can use.

HOW PYTHON CALLS AN EDGE FUNCTION
-----------------------------------
An Edge Function is just an HTTPS endpoint. We POST a small JSON body
to `{SUPABASE_URL}/functions/v1/validate-document` with an
Authorization header (Supabase requires a valid API key on that header
even though our function itself doesn't check user identity), and we
get back JSON. No special SDK magic is required — it's a plain HTTP
call, which is exactly what makes Edge Functions usable from any
language or client.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from app.config import settings


@dataclass
class ValidationResult:
    valid: bool
    normalized_category: str | None = None
    validation_tag: str | None = None
    errors: list[str] | None = None


class EdgeFunctionError(Exception):
    """Raised when the Edge Function is unreachable or returns something unexpected."""


def validate_document(file_name: str, file_type: str, file_size: int, category: str) -> ValidationResult:
    """
    Calls the `validate-document` Edge Function and returns a
    ValidationResult. Raises EdgeFunctionError on network failure or an
    unexpected (non-JSON) response, so callers can show a friendly
    message instead of crashing.
    """
    payload = {
        "file_name": file_name,
        "file_type": file_type,
        "file_size": file_size,
        "category": category,
    }

    headers = {
        "Content-Type": "application/json",
        # The Edge Function is deployed with default JWT verification,
        # so Supabase expects a valid API key on this header even though
        # our function's own logic doesn't check *who* the user is.
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }

    try:
        response = requests.post(
            settings.edge_function_url,
            json=payload,
            headers=headers,
            timeout=15,
        )
    except requests.exceptions.RequestException as exc:
        raise EdgeFunctionError(
            f"Could not reach the Edge Function at {settings.edge_function_url}. "
            f"Is it deployed? (supabase functions deploy validate-document). "
            f"Original error: {exc}"
        ) from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise EdgeFunctionError(
            f"Edge Function returned a non-JSON response (status {response.status_code}): "
            f"{response.text[:300]}"
        ) from exc

    if response.status_code not in (200, 400, 422):
        raise EdgeFunctionError(
            f"Edge Function returned unexpected status {response.status_code}: {body}"
        )

    if body.get("valid"):
        data = body.get("data", {})
        return ValidationResult(
            valid=True,
            normalized_category=data.get("normalized_category"),
            validation_tag=data.get("validation_tag"),
        )

    return ValidationResult(valid=False, errors=body.get("errors", ["Unknown validation error."]))
