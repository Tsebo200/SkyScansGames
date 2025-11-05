#!/usr/bin/env python3
"""
Backfill games.release_date (YYYY-MM-DD) and release_year from RAWG for existing rows.

This script updates the SQLite database directly and does not require restarting the API server.
It reads RAWG_API_KEY from environment (optional). If missing or unauthorized, rows will be skipped.

Usage:
  python backend/scripts/backfill_release_dates.py --limit 200
  python backend/scripts/backfill_release_dates.py --db /path/to/skyscans_games.db
"""
import argparse
import json
import os
import sqlite3
import sys
import time
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError


def ensure_column(conn: sqlite3.Connection, table: str, column: str, coltype: str):
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def fetch_rawg_details(rawg_id: int, api_key: str | None, timeout: float = 10.0) -> dict:
    base = f"https://api.rawg.io/api/games/{rawg_id}"
    params = {"key": api_key} if api_key else {}
    url = base + ("?" + urlencode(params) if params else "")
    try:
        with urlopen(url, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except HTTPError as e:
        sys.stderr.write(f"RAWG HTTPError for {rawg_id}: {e}\n")
    except URLError as e:
        sys.stderr.write(f"RAWG URLError for {rawg_id}: {e}\n")
    except Exception as e:
        sys.stderr.write(f"RAWG fetch error for {rawg_id}: {e}\n")
    return {}


def main():
    parser = argparse.ArgumentParser()
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
    default_db = os.path.join(repo_root, "skyscans_games.db")
    parser.add_argument("--db", default=default_db, help="Path to SQLite DB (default: repo root skyscans_games.db)")
    parser.add_argument("--limit", type=int, default=200, help="Max rows to process (default 200, set -1 for all)")
    parser.add_argument("--sleep", type=float, default=0.15, help="Sleep seconds between API calls (default 0.15)")
    args = parser.parse_args()

    api_key = os.getenv("RAWG_API_KEY")
    db_path = args.db
    lim = None if args.limit is None or args.limit < 0 else args.limit

    if not os.path.exists(db_path):
        print(f"DB not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Ensure release_date column exists
        ensure_column(conn, "games", "release_date", "TEXT")
        conn.commit()

        query = "SELECT id, rawg_id, release_date, release_year FROM games WHERE rawg_id IS NOT NULL AND (release_date IS NULL OR release_year IS NULL) ORDER BY id ASC"
        if lim is not None:
            query += f" LIMIT {int(lim)}"
        rows = conn.execute(query).fetchall()
        if not rows:
            print("No rows require backfill.")
            return
        updated = 0
        for r in rows:
            gid = r["id"]
            rid = r["rawg_id"]
            details = fetch_rawg_details(int(rid), api_key)
            rel = details.get("released") if isinstance(details, dict) else None
            if isinstance(rel, str) and len(rel) >= 4:
                # Update release_date
                conn.execute("UPDATE games SET release_date = COALESCE(release_date, ?), updated_at = CURRENT_TIMESTAMP WHERE id = ?", (rel, gid))
                # Update release_year if missing
                try:
                    year = int(rel[:4])
                    conn.execute("UPDATE games SET release_year = COALESCE(release_year, ?), updated_at = CURRENT_TIMESTAMP WHERE id = ?", (year, gid))
                except Exception:
                    pass
                updated += 1
                if updated % 25 == 0:
                    conn.commit()
                time.sleep(max(0.0, args.sleep))
        conn.commit()
        print(json.dumps({"updated": updated}))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
