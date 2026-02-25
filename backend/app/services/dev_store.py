"""
In-memory storage for development mode.

Replaces Supabase when SUPABASE_SERVICE_KEY is a placeholder.
Implements the same builder-pattern interface as the Supabase Python client
so existing code works without changes.
"""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from typing import Any


class _DevResponse:
    """Mimics Supabase execute() response."""

    def __init__(self, data: Any = None, count: int | None = None):
        self.data = data
        self.count = count


class _DevQueryBuilder:
    """
    Fluent query builder that mimics supabase-py's PostgREST interface.

    Supports: select, insert, update, upsert, delete + eq, gte, or_, order, range, limit, single, maybe_single.
    """

    def __init__(self, store: "_DevStore", table: str, op: str, **kwargs):
        self._store = store
        self._table = table
        self._op = op
        self._select_cols: str = kwargs.get("cols", "*")
        self._count_mode: str | None = kwargs.get("count_mode")
        self._filters: list[tuple[str, str, Any]] = []
        self._order_col: str | None = None
        self._order_desc: bool = False
        self._range_start: int | None = None
        self._range_end: int | None = None
        self._limit_n: int | None = None
        self._is_single: bool = False
        self._is_maybe_single: bool = False
        self._payload: Any = kwargs.get("payload")
        self._on_conflict: str | None = kwargs.get("on_conflict")

    # ── Filter methods ─────────────────────────────────────────

    def eq(self, col: str, val: Any) -> "_DevQueryBuilder":
        self._filters.append(("eq", col, val))
        return self

    def gte(self, col: str, val: Any) -> "_DevQueryBuilder":
        self._filters.append(("gte", col, val))
        return self

    def or_(self, expr: str) -> "_DevQueryBuilder":
        # Simplified: ignore complex OR filters in dev mode
        return self

    # ── Modifiers ──────────────────────────────────────────────

    def order(self, col: str, desc: bool = False) -> "_DevQueryBuilder":
        self._order_col = col
        self._order_desc = desc
        return self

    def range(self, start: int, end: int) -> "_DevQueryBuilder":
        self._range_start = start
        self._range_end = end
        return self

    def limit(self, n: int) -> "_DevQueryBuilder":
        self._limit_n = n
        return self

    def single(self) -> "_DevQueryBuilder":
        self._is_single = True
        return self

    def maybe_single(self) -> "_DevQueryBuilder":
        self._is_maybe_single = True
        return self

    # ── Execution ──────────────────────────────────────────────

    def execute(self) -> _DevResponse:
        if self._op == "select":
            return self._exec_select()
        elif self._op == "insert":
            return self._exec_insert()
        elif self._op == "update":
            return self._exec_update()
        elif self._op == "upsert":
            return self._exec_upsert()
        elif self._op == "delete":
            return self._exec_delete()
        return _DevResponse()

    # ── Select ─────────────────────────────────────────────────

    def _exec_select(self) -> _DevResponse:
        rows = self._store._get_table(self._table)
        rows = self._apply_filters(rows)

        if self._order_col:
            rows.sort(
                key=lambda r: r.get(self._order_col, ""),
                reverse=self._order_desc,
            )

        total = len(rows)

        if self._range_start is not None and self._range_end is not None:
            rows = rows[self._range_start : self._range_end + 1]
        if self._limit_n is not None:
            rows = rows[: self._limit_n]

        # Deep-copy to avoid mutation
        rows = copy.deepcopy(rows)

        # Handle join-like selects (e.g., "*, videos(...)")
        # For dev mode, attach related data inline
        if "videos(" in self._select_cols and self._table == "study_guides":
            videos_table = self._store._get_table("videos")
            for row in rows:
                vid = row.get("video_id", "")
                matching = [v for v in videos_table if v.get("youtube_id") == vid]
                row["videos"] = matching[0] if matching else {}

        if self._is_single or self._is_maybe_single:
            if rows:
                return _DevResponse(data=rows[0], count=total)
            if self._is_maybe_single:
                return _DevResponse(data=None, count=0)
            return _DevResponse(data=None, count=0)

        return _DevResponse(data=rows, count=total)

    # ── Insert ─────────────────────────────────────────────────

    def _exec_insert(self) -> _DevResponse:
        table = self._store._get_table(self._table)
        row = copy.deepcopy(self._payload)
        table.append(row)
        return _DevResponse(data=[row], count=1)

    # ── Update ─────────────────────────────────────────────────

    def _exec_update(self) -> _DevResponse:
        table = self._store._get_table(self._table)
        updated = []
        for row in table:
            if self._matches(row):
                row.update(self._payload)
                updated.append(row)
        return _DevResponse(data=updated, count=len(updated))

    # ── Upsert ─────────────────────────────────────────────────

    def _exec_upsert(self) -> _DevResponse:
        table = self._store._get_table(self._table)
        conflict_col = self._on_conflict or "id"
        conflict_val = self._payload.get(conflict_col)

        existing = [r for r in table if r.get(conflict_col) == conflict_val]
        if existing:
            existing[0].update(self._payload)
            return _DevResponse(data=[existing[0]], count=1)
        else:
            row = copy.deepcopy(self._payload)
            table.append(row)
            return _DevResponse(data=[row], count=1)

    # ── Delete ─────────────────────────────────────────────────

    def _exec_delete(self) -> _DevResponse:
        table = self._store._get_table(self._table)
        to_remove = [r for r in table if self._matches(r)]
        for r in to_remove:
            table.remove(r)
        return _DevResponse(data=to_remove, count=len(to_remove))

    # ── Helpers ────────────────────────────────────────────────

    def _apply_filters(self, rows: list[dict]) -> list[dict]:
        return [r for r in rows if self._matches(r)]

    def _matches(self, row: dict) -> bool:
        for op, col, val in self._filters:
            row_val = row.get(col)
            if op == "eq" and row_val != val:
                return False
            if op == "gte" and (row_val is None or str(row_val) < str(val)):
                return False
        return True


class _DevRpcBuilder:
    """Mimics supabase-py's RPC call interface."""

    def __init__(self, store: "_DevStore", fn_name: str, params: dict):
        self._store = store
        self._fn = fn_name
        self._params = params

    def execute(self) -> _DevResponse:
        # Handle known RPC functions
        if self._fn == "deduct_credits":
            user_id = self._params.get("p_user_id")
            cost = self._params.get("p_cost", 0)
            profiles = self._store._get_table("profiles")
            for p in profiles:
                if p.get("id") == user_id:
                    p["credits_used"] = p.get("credits_used", 0) + cost
                    return _DevResponse(data=[p])
            return _DevResponse(data=[])
        return _DevResponse(data=[])


class _DevTableProxy:
    """Returned by DevStore.table() — provides select/insert/update/delete/upsert."""

    def __init__(self, store: "_DevStore", table_name: str):
        self._store = store
        self._table = table_name

    def select(self, cols: str = "*", count: str | None = None) -> _DevQueryBuilder:
        return _DevQueryBuilder(
            self._store, self._table, "select", cols=cols, count_mode=count
        )

    def insert(self, payload: dict | list) -> _DevQueryBuilder:
        return _DevQueryBuilder(
            self._store, self._table, "insert", payload=payload
        )

    def update(self, payload: dict) -> _DevQueryBuilder:
        return _DevQueryBuilder(
            self._store, self._table, "update", payload=payload
        )

    def upsert(self, payload: dict, on_conflict: str | None = None) -> _DevQueryBuilder:
        return _DevQueryBuilder(
            self._store, self._table, "upsert", payload=payload, on_conflict=on_conflict
        )

    def delete(self) -> _DevQueryBuilder:
        return _DevQueryBuilder(self._store, self._table, "delete")


class _DevStore:
    """
    Singleton in-memory store that replaces Supabase in dev mode.

    Usage:
        client = get_dev_client()
        client.table("processing_jobs").insert({...}).execute()
    """

    def __init__(self):
        self._tables: dict[str, list[dict]] = {}
        # Seed a dev user profile
        self._tables["profiles"] = [
            {
                "id": "dev-user-001",
                "email": "dev@mindmesh.local",
                "tier": "pro",  # Give dev user pro features
                "credits_used": 0,
                "daily_credit_limit": 999,
                "credits_reset_at": "2099-12-31T23:59:59Z",
            }
        ]

    def _get_table(self, name: str) -> list[dict]:
        if name not in self._tables:
            self._tables[name] = []
        return self._tables[name]

    def table(self, name: str) -> _DevTableProxy:
        return _DevTableProxy(self, name)

    def rpc(self, fn_name: str, params: dict | None = None) -> _DevRpcBuilder:
        return _DevRpcBuilder(self, fn_name, params or {})


# ── Singleton ──────────────────────────────────────────────────

_instance: _DevStore | None = None


def get_dev_client() -> _DevStore:
    """Get the singleton dev store client (replaces Supabase in dev mode)."""
    global _instance
    if _instance is None:
        _instance = _DevStore()
    return _instance


def is_dev_mode() -> bool:
    """Check if we're running in dev mode (placeholder Supabase keys)."""
    from app.config import get_settings

    settings = get_settings()
    return (
        settings.environment == "development"
        and settings.supabase_service_key.startswith("your-")
    )
