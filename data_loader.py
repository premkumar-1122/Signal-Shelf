"""
data_loader.py — DuckDB ingest, normalization, FTS index, and caching layer.

Reads the CSV into DuckDB on startup, keyed on the CSV's mtime so any
edit to the file triggers a transparent reload on the next Streamlit rerun.
"""

import os
import re
import json
import duckdb
import streamlit as st
import pandas as pd
import hashlib
import logging
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path to the single-source-of-truth JSONL
# ---------------------------------------------------------------------------
JSONL_PATH = Path(__file__).parent / "Resources" / "resource_database.jsonl"

# ---------------------------------------------------------------------------
# Newsletter canonical-name map (handles inconsistent casing)
# ---------------------------------------------------------------------------
_NEWSLETTER_CANONICAL = {
    "ai for work":        "AI For Work",
    "deepview":           "DeepView",
    "the deep view":      "DeepView",
    "superhuman ai":      "Superhuman AI",
    "the rundown ai":     "The Rundown AI",
    "tldr":               "TLDR",
    "tldr ai":            "TLDR AI",
    "tldr data":          "TLDR Data",
    "stayingahead daily": "StayingAhead Daily",
}

# ---------------------------------------------------------------------------
# Persona splitting — commas, ampersands, slashes, and the word "and"
# ---------------------------------------------------------------------------
_PERSONA_SPLIT_RE = re.compile(r"\s*[,&/]\s*|\s+and\s+", re.IGNORECASE)


def _normalize_newsletter(raw: str) -> str:
    """Map any casing variant to its canonical newsletter name."""
    key = raw.strip().lower()
    return _NEWSLETTER_CANONICAL.get(key, raw.strip())


def _parse_date(raw: str):
    """
    Try DD-MM-YYYY.  Return (date_obj | None, is_known: bool).
    'unknown', 'Q2 2026', or anything unparseable → (None, False).
    Legitimate 2024 dates parse normally.
    """
    val = raw.strip()
    if not val or val.lower() == "unknown":
        return None, False
    try:
        dt = datetime.strptime(val, "%d-%m-%Y")
        return dt.date(), True
    except ValueError:
        return None, False


def _split_personas(raw: str) -> list[str]:
    """Split a combined persona string into clean atomic tags."""
    if not raw or not raw.strip():
        return []
    parts = _PERSONA_SPLIT_RE.split(raw.strip())
    tags = []
    for p in parts:
        p = p.strip()
        if p:
            tags.append(p)
    return tags


def _parse_newsletters(raw: str) -> list[str]:
    """Split comma-separated newsletters and normalize each component."""
    if not raw or not raw.strip():
        return []
    parts = raw.split(",")
    nls = []
    for p in parts:
        p = p.strip()
        if p:
            nls.append(_normalize_newsletter(p))
    return nls


# ---------------------------------------------------------------------------
# JSONL mtime/hash helpers
# ---------------------------------------------------------------------------
def get_jsonl_mtime() -> float:
    """Return the JSONL's last-modified timestamp (epoch seconds)."""
    try:
        return os.path.getmtime(JSONL_PATH)
    except OSError:
        return 0.0


def get_jsonl_hash() -> str:
    """Return the MD5 hash of the JSONL file."""
    hasher = hashlib.md5()
    try:
        with open(JSONL_PATH, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except OSError:
        return ""


def _normalize_row(r):
    """Normalize a JSONL row into database columns schema format."""
    raw_newsletter = r.get("source_newsletter", "").strip()
    newsletter_tags = _parse_newsletters(raw_newsletter)
    newsletter_text = ", ".join(newsletter_tags)
    parsed_date, is_date_known = _parse_date(r.get("date_of_appearance", ""))
    persona_raw = r.get("target_persona", "").strip()
    persona_tags = _split_personas(persona_raw)
    sponsored = str(r.get("sponsored_content", "")).strip().lower() == "yes"

    return {
        "sno":                    int(r["s_no"]),
        "source_newsletters":     newsletter_tags,
        "source_newsletter_text": newsletter_text,
        "date_raw":               str(r.get("date_of_appearance", "")).strip(),
        "parsed_date":            parsed_date,
        "is_date_known":          is_date_known,
        "content_type":           str(r.get("content_type", "")).strip(),
        "theme":                  str(r.get("theme", "")).strip(),
        "extracted_content":      str(r.get("extracted_content", "")).strip(),
        "sponsored":              sponsored,
        "target_persona_raw":     persona_raw,
        "persona_tags":           persona_tags,
        "setup_time":             str(r.get("estimated_setup_time", "")).strip(),
    }


# Track sync states in module-level variables
_last_mtime = 0.0
_last_hash = ""
_db_lock = threading.Lock()


def sync_database(con):
    """
    Sync JSONL file content to DuckDB entries table.
    Gracefully handles malformed rows by logging warnings and capturing errors.
    """
    global _last_mtime, _last_hash

    current_mtime = get_jsonl_mtime()
    current_hash = get_jsonl_hash()

    # Check if table entries exists and count > 0 to verify it is populated
    table_exists = False
    try:
        table_exists = con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'entries'"
        ).fetchone()[0] > 0
    except Exception:
        pass

    if table_exists and current_mtime == _last_mtime and current_hash == _last_hash:
        return  # No changes detected, skip sync

    with _db_lock:
        logger.info("Syncing DuckDB table with JSONL data...")
        _last_mtime = current_mtime
        _last_hash = current_hash

        # 1. Create table if not exists
        con.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                sno                     INTEGER PRIMARY KEY,
                source_newsletters      VARCHAR[],
                source_newsletter_text  VARCHAR,
                date_raw                VARCHAR,
                parsed_date             DATE,
                is_date_known           BOOLEAN,
                content_type            VARCHAR,
                theme                   VARCHAR,
                extracted_content       VARCHAR,
                sponsored               BOOLEAN,
                target_persona_raw      VARCHAR,
                persona_tags            VARCHAR[],
                setup_time              VARCHAR
            )
        """)

        # 2. Parse JSONL file line-by-line
        jsonl_rows = {}
        ingestion_errors = []

        if JSONL_PATH.exists():
            with open(JSONL_PATH, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                        if "s_no" not in row or row["s_no"] is None:
                            raise KeyError("Missing or null 's_no' field")
                        sno = int(row["s_no"])
                        # Verify required fields exist
                        required_fields = [
                            "source_newsletter", "date_of_appearance", "content_type",
                            "theme", "extracted_content", "sponsored_content",
                            "target_persona", "estimated_setup_time"
                        ]
                        for field in required_fields:
                            if field not in row:
                                raise KeyError(f"Missing field '{field}'")

                        if sno in jsonl_rows:
                            msg = f"Line {line_num}: Duplicate s_no {sno} found in JSONL. Overwriting."
                            logger.warning(msg)
                            ingestion_errors.append(msg)

                        jsonl_rows[sno] = _normalize_row(row)
                    except Exception as e:
                        msg = f"Line {line_num}: {str(e)}"
                        logger.warning(f"Error parsing JSONL line: {msg}")
                        ingestion_errors.append(msg)
        else:
            msg = f"JSONL file not found at {JSONL_PATH}"
            logger.warning(msg)
            ingestion_errors.append(msg)

        # Store errors in session state so Streamlit UI can surface them
        st.session_state["ingestion_errors"] = ingestion_errors

        # 3. Retrieve DB rows
        db_rows = con.execute("SELECT * FROM entries").fetchall()
        db_dict = {}
        for r in db_rows:
            db_dict[r[0]] = {
                "sno": r[0],
                "source_newsletters": list(r[1]) if r[1] is not None else [],
                "source_newsletter_text": r[2],
                "date_raw": r[3],
                "parsed_date": r[4],
                "is_date_known": r[5],
                "content_type": r[6],
                "theme": r[7],
                "extracted_content": r[8],
                "sponsored": r[9],
                "target_persona_raw": r[10],
                "persona_tags": list(r[11]) if r[11] is not None else [],
                "setup_time": r[12]
            }

        # 4. Compare and find changes
        to_delete = [sno for sno in db_dict if sno not in jsonl_rows]
        to_insert = [jsonl_rows[sno] for sno in jsonl_rows if sno not in db_dict]
        to_update = []
        for sno in jsonl_rows:
            if sno in db_dict:
                if jsonl_rows[sno] != db_dict[sno]:
                    to_update.append(jsonl_rows[sno])

        # 5. Apply changes to DB
        any_changes = False

        if to_delete:
            logger.info(f"Sync: Deleting {len(to_delete)} removed entries from DuckDB: {to_delete}")
            con.executemany("DELETE FROM entries WHERE sno = ?", [(sno,) for sno in to_delete])
            any_changes = True

        if to_insert:
            logger.info(f"Sync: Inserting {len(to_insert)} new entries into DuckDB")
            con.executemany(
                """INSERT INTO entries VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )""",
                [
                    (
                        r["sno"],
                        r["source_newsletters"],
                        r["source_newsletter_text"],
                        r["date_raw"],
                        r["parsed_date"],
                        r["is_date_known"],
                        r["content_type"],
                        r["theme"],
                        r["extracted_content"],
                        r["sponsored"],
                        r["target_persona_raw"],
                        r["persona_tags"],
                        r["setup_time"],
                    )
                    for r in to_insert
                ],
            )
            any_changes = True

        if to_update:
            logger.info(f"Sync: Updating {len(to_update)} modified entries in DuckDB")
            con.executemany(
                """UPDATE entries SET
                    source_newsletters = ?,
                    source_newsletter_text = ?,
                    date_raw = ?,
                    parsed_date = ?,
                    is_date_known = ?,
                    content_type = ?,
                    theme = ?,
                    extracted_content = ?,
                    sponsored = ?,
                    target_persona_raw = ?,
                    persona_tags = ?,
                    setup_time = ?
                WHERE sno = ?""",
                [
                    (
                        r["source_newsletters"],
                        r["source_newsletter_text"],
                        r["date_raw"],
                        r["parsed_date"],
                        r["is_date_known"],
                        r["content_type"],
                        r["theme"],
                        r["extracted_content"],
                        r["sponsored"],
                        r["target_persona_raw"],
                        r["persona_tags"],
                        r["setup_time"],
                        r["sno"],
                    )
                    for r in to_update
                ],
            )
            any_changes = True

        # 6. Rebuild FTS if changes occurred or if FTS is missing
        fts_available = False
        if any_changes or not st.session_state.get("fts_index_created", False):
            try:
                con.execute("INSTALL fts")
                con.execute("LOAD fts")
                con.execute("""
                    PRAGMA create_fts_index(
                        'entries',
                        'sno',
                        'extracted_content', 'theme', 'content_type', 'source_newsletter_text',
                        overwrite = 1
                    )
                """)
                fts_available = True
                st.session_state["fts_index_created"] = True
                logger.info("FTS index built/updated successfully")
            except Exception as e:
                logger.error(f"Failed to build FTS index: {e}")
                fts_available = False
                st.session_state["fts_index_created"] = False
        else:
            fts_available = st.session_state.get("fts_available", False)

        st.session_state["fts_available"] = fts_available


LOCAL_DB_PATH = Path(__file__).parent / "local_cache.duckdb"


def _connect_motherduck(token: str, database: str) -> duckdb.DuckDBPyConnection:
    """Attempt a MotherDuck remote connection."""
    os.environ["motherduck_token"] = token
    try:
        con = duckdb.connect()
        con.execute("INSTALL motherduck")
        con.execute("LOAD motherduck")
    except Exception:
        pass  # extension may already be available
    return duckdb.connect(f"md:{database}")


def _connect_local() -> duckdb.DuckDBPyConnection:
    """Fall back to a persistent local DuckDB file."""
    logger.info("Falling back to local DuckDB database.")
    return duckdb.connect(str(LOCAL_DB_PATH))


@st.cache_resource
def get_connection():
    """Create and cache a database connection — MotherDuck remote, or local fallback."""
    token = st.secrets.get("motherduck", {}).get("token")
    database = st.secrets.get("motherduck", {}).get("database")

    if token and token.strip() and database and database.strip() and database != "YOUR DATBASE HERE":
        try:
            return _connect_motherduck(token, database)
        except Exception as e:
            logger.warning(f"MotherDuck connection failed: {e}. Falling back to local DB.")

    return _connect_local()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_db():
    """
    Return (duckdb.Connection, fts_available).
    Use remote MotherDuck if available (data synced via sync_to_motherduck.py).
    Fall back to local DuckDB populated from JSONL when MotherDuck is unreachable.
    """
    con = get_connection()

    # Only sync from JSONL if the entries table is missing or empty
    table_has_data = False
    try:
        count = con.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        table_has_data = count > 0
    except Exception:
        pass

    if not table_has_data:
        sync_database(con)

    fts_available = False
    try:
        res = con.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'fts_main_entries'"
        ).fetchone()
        fts_available = res[0] > 0 if res else False
    except Exception:
        fts_available = False

    return con, fts_available


def query_entries(
    con,
    fts_available: bool,
    search_term: str = "",
    newsletters: list[str] | None = None,
    date_range: tuple | None = None,
    single_date=None,
    include_unknown_dates: bool = True,
    content_types: list[str] | None = None,
    themes: list[str] | None = None,
    sponsored_filter: str = "All",          # "All" | "Hide Sponsored" | "Sponsored Only"
    persona_tags: list[str] | None = None,
    setup_times: list[str] | None = None,
    sort_by: str = "Date (Newest First)",
) -> pd.DataFrame:
    """
    Build and execute a filtered + sorted query.  Returns a pandas DataFrame.
    Every filter is AND-combined.  All option lists are dynamic from DuckDB.
    """
    conditions = []
    params = {}

    # --- Search -----------------------------------------------------------
    if search_term and search_term.strip():
        term = search_term.strip()
        if fts_available:
            # DuckDB FTS — score-based retrieval
            conditions.append("""
                sno IN (
                    SELECT sno FROM (
                        SELECT *, fts_main_entries.match_bm25(sno, $search_term) AS score
                        FROM entries
                    ) WHERE score IS NOT NULL
                )
            """)
            params["search_term"] = term
        else:
            # ILIKE fallback
            like_pat = f"%{term}%"
            conditions.append("""(
                extracted_content ILIKE $like_pat
                OR theme ILIKE $like_pat
                OR content_type ILIKE $like_pat
                OR source_newsletter_text ILIKE $like_pat
            )""")
            params["like_pat"] = like_pat

    # --- Newsletter -------------------------------------------------------
    if newsletters:
        nl_conditions = []
        for i, nl in enumerate(newsletters):
            nl_conditions.append(f"list_contains(source_newsletters, $nl_{i})")
            params[f"nl_{i}"] = nl
        conditions.append(f"({' OR '.join(nl_conditions)})")

    # --- Date range / Single date -----------------------------------------
    if single_date:
        if include_unknown_dates:
            conditions.append(
                "(parsed_date = $single_date OR is_date_known = false)"
            )
        else:
            conditions.append(
                "parsed_date = $single_date"
            )
        params["single_date"] = single_date
    elif date_range and len(date_range) == 2:
        start_date, end_date = date_range
        if include_unknown_dates:
            conditions.append(
                "(parsed_date BETWEEN $start_date AND $end_date OR is_date_known = false)"
            )
        else:
            conditions.append(
                "parsed_date BETWEEN $start_date AND $end_date"
            )
        params["start_date"] = start_date
        params["end_date"] = end_date
    elif not include_unknown_dates:
        conditions.append("is_date_known = true")

    # --- Content type -----------------------------------------------------
    if content_types:
        placeholders = ", ".join(f"$ct_{i}" for i in range(len(content_types)))
        conditions.append(f"content_type IN ({placeholders})")
        for i, ct in enumerate(content_types):
            params[f"ct_{i}"] = ct

    # --- Theme ------------------------------------------------------------
    if themes:
        placeholders = ", ".join(f"$th_{i}" for i in range(len(themes)))
        conditions.append(f"theme IN ({placeholders})")
        for i, th in enumerate(themes):
            params[f"th_{i}"] = th

    # --- Sponsored --------------------------------------------------------
    if sponsored_filter == "Hide Sponsored":
        conditions.append("sponsored = false")
    elif sponsored_filter == "Sponsored Only":
        conditions.append("sponsored = true")

    # --- Persona tags (ANY match — if the row contains at least one tag) --
    if persona_tags:
        tag_conditions = []
        for i, tag in enumerate(persona_tags):
            tag_conditions.append(f"list_contains(persona_tags, $pt_{i})")
            params[f"pt_{i}"] = tag
        conditions.append(f"({' OR '.join(tag_conditions)})")

    # --- Setup time -------------------------------------------------------
    if setup_times:
        placeholders = ", ".join(f"$st_{i}" for i in range(len(setup_times)))
        conditions.append(f"setup_time IN ({placeholders})")
        for i, st_val in enumerate(setup_times):
            params[f"st_{i}"] = st_val

    # --- Build WHERE clause -----------------------------------------------
    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    # --- Sorting ----------------------------------------------------------
    setup_order_asc = """
        CASE setup_time
            WHEN 'Instant < 2 mins' THEN 1
            WHEN 'Quick 5-10 mins' THEN 2
            WHEN 'Deep Setup > 30 mins' THEN 3
            ELSE 4
        END
    """
    sort_map = {
        "Date (Newest First)":       "is_date_known DESC, parsed_date DESC NULLS LAST, sno ASC",
        "Date (Oldest First)":       "is_date_known DESC, parsed_date ASC NULLS LAST, sno ASC",
        "Newsletter A → Z":         "source_newsletter_text ASC, sno ASC",
        "Setup Time (Quickest)":     f"{setup_order_asc} ASC, sno ASC",
        "Setup Time (Most Involved)": f"{setup_order_asc} DESC, sno ASC",
    }
    order = sort_map.get(sort_by, "sno ASC")

    sql = f"SELECT * FROM entries {where} ORDER BY {order}"
    result = con.execute(sql, params).fetchdf()
    return result


def get_filter_options(con) -> dict:
    """Derive all filter option lists dynamically from current DuckDB data."""
    newsletters = con.execute(
        "SELECT DISTINCT UNNEST(source_newsletters) AS nl FROM entries ORDER BY nl"
    ).fetchall()
    content_types = con.execute(
        "SELECT DISTINCT content_type FROM entries ORDER BY content_type"
    ).fetchall()
    themes = con.execute(
        "SELECT DISTINCT theme FROM entries ORDER BY theme"
    ).fetchall()
    setup_times_raw = con.execute(
        "SELECT DISTINCT setup_time FROM entries"
    ).fetchall()
    # Persona tags — unnest the list column
    persona_tags = con.execute(
        "SELECT DISTINCT UNNEST(persona_tags) AS tag FROM entries ORDER BY tag"
    ).fetchall()

    # Determine date range from known dates
    date_bounds = con.execute(
        "SELECT MIN(parsed_date), MAX(parsed_date) FROM entries WHERE is_date_known = true"
    ).fetchone()

    # Order setup times logically
    setup_order = ["Instant < 2 mins", "Quick 5-10 mins", "Deep Setup > 30 mins"]
    raw_times = [r[0] for r in setup_times_raw]
    ordered_times = [t for t in setup_order if t in raw_times]
    # append any unexpected values
    for t in raw_times:
        if t not in ordered_times:
            ordered_times.append(t)

    return {
        "newsletters":   [r[0] for r in newsletters],
        "content_types": [r[0] for r in content_types],
        "themes":        [r[0] for r in themes],
        "setup_times":   ordered_times,
        "persona_tags":  [r[0] for r in persona_tags],
        "date_min":      date_bounds[0] if date_bounds else None,
        "date_max":      date_bounds[1] if date_bounds else None,
    }


def get_stats(con) -> dict:
    """Live stats for the hero section."""
    row = con.execute("""
        SELECT
            COUNT(*) AS total,
            (SELECT COUNT(DISTINCT nl) FROM (SELECT UNNEST(source_newsletters) AS nl FROM entries)) AS sources,
            COUNT(DISTINCT theme) AS themes
        FROM entries
    """).fetchone()
    return {
        "total_entries": row[0],
        "total_sources": row[1],
        "total_themes":  row[2],
        "last_updated":  datetime.fromtimestamp(get_jsonl_mtime()).strftime("%b %d, %Y at %H:%M"),
    }
