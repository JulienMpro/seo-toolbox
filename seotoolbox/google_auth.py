"""Shared OAuth helpers for Google API connectors."""

from __future__ import annotations

import os

import httpx

TOKEN_URL = "https://oauth2.googleapis.com/token"


def get_access_token() -> str:
    """Exchange the configured Google refresh token for an access token."""
    names = ("GSC_CLIENT_ID", "GSC_CLIENT_SECRET", "GSC_REFRESH_TOKEN")
    values = [os.getenv(name) for name in names]
    if not all(values):
        raise ValueError("GSC credentials missing")

    response = httpx.post(
        TOKEN_URL,
        data={
            "client_id": values[0],
            "client_secret": values[1],
            "refresh_token": values[2],
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"Google OAuth token request failed: {response.text}") from exc
    token = response.json().get("access_token")
    if not token:
        raise ValueError("GSC access token missing from OAuth response")
    return str(token)
