"""Cached DataForSEO HTTP client shared by all toolbox modules."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable

import httpx


class DataForSEOError(RuntimeError):
    """Raised when DataForSEO reports a task-level business error."""


class ApiError(RuntimeError):
    """Raised when DataForSEO cannot be reached or returns invalid HTTP data."""


class DataForSEOClient:
    """Small DataForSEO client with mandatory SQLite caching and retries."""

    base_url = "https://api.dataforseo.com/v3/"

    def __init__(
        self,
        *,
        username: str | None = None,
        password: str | None = None,
        cache_path: str | Path = "data/cache.db",
        cache_ttl: float = 24 * 60 * 60,
        timeout: float = 30.0,
        retries: int = 3,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.username = username if username is not None else os.getenv("DATAFORSEO_USERNAME")
        self.password = password if password is not None else os.getenv("DATAFORSEO_PASSWORD")
        self.cache_path = Path(cache_path)
        self.cache_ttl = cache_ttl
        self.timeout = timeout
        self.retries = retries
        self.transport = transport
        self.sleep = sleep

    def _connect(self) -> sqlite3.Connection:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.cache_path)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS cache "
            "(hash TEXT PRIMARY KEY, response TEXT NOT NULL, ts REAL NOT NULL)"
        )
        return connection

    @staticmethod
    def _cache_key(path: str, payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha1(f"POST{path}{canonical}".encode()).hexdigest()

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST one live task, returning a cached response whenever possible."""
        normalized_path = path.lstrip("/")
        key = self._cache_key(normalized_path, payload)
        now = time.time()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT response, ts FROM cache WHERE hash = ?", (key,)
            ).fetchone()
            if row and now - float(row[1]) < self.cache_ttl:
                try:
                    return json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    connection.execute("DELETE FROM cache WHERE hash = ?", (key,))

        if not self.username or not self.password:
            raise ApiError(
                "Missing DataForSEO credentials. Set DATAFORSEO_USERNAME and "
                "DATAFORSEO_PASSWORD before making API requests."
            )

        last_error: Exception | None = None
        try:
            with httpx.Client(
                base_url=self.base_url,
                auth=(self.username, self.password),
                timeout=self.timeout,
                transport=self.transport,
            ) as http:
                for attempt in range(self.retries):
                    try:
                        response = http.post(normalized_path, json=[payload])
                        if response.status_code == 429 or response.status_code >= 500:
                            if attempt + 1 < self.retries:
                                self.sleep(2**attempt)
                                continue
                        response.raise_for_status()
                        data = response.json()
                        if not isinstance(data, dict):
                            raise ApiError("DataForSEO returned an unexpected response format.")
                        with self._connect() as connection:
                            connection.execute(
                                "INSERT OR REPLACE INTO cache(hash, response, ts) VALUES (?, ?, ?)",
                                (key, json.dumps(data), now),
                            )
                        return data
                    except (httpx.HTTPError, ValueError) as exc:
                        last_error = exc
                        if attempt + 1 < self.retries and isinstance(
                            exc, (httpx.ConnectError, httpx.TimeoutException)
                        ):
                            self.sleep(2**attempt)
                            continue
                        break
        except httpx.HTTPError as exc:
            last_error = exc
        raise ApiError(f"DataForSEO request failed: {last_error}") from last_error

    def get_result(self, path: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Validate task statuses and flatten their result arrays."""
        response = self.post(path, payload)
        tasks = response.get("tasks")
        if not isinstance(tasks, list):
            raise ApiError("DataForSEO response does not contain a valid tasks list.")
        flattened: list[dict[str, Any]] = []
        for task in tasks:
            if not isinstance(task, dict):
                raise ApiError("DataForSEO returned an invalid task.")
            if task.get("status_code") != 20000:
                message = task.get("status_message") or "Unknown DataForSEO task error"
                raise DataForSEOError(str(message))
            result = task.get("result") or []
            if isinstance(result, list):
                flattened.extend(item for item in result if isinstance(item, dict))
            elif isinstance(result, dict):
                flattened.append(result)
        return flattened

