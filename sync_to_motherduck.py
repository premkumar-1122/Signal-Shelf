import os
import re
import json
import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

# Path to local JSONL file
JSONL_PATH = Path("Resources") / "resource_database.jsonl"

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

_PERSONA_SPLIT_RE = re.compile(r"\s*[,&/]\s*|\s+and\s+", re.IGNORECASE)

def _normalize_newsletter(raw: str) -> str:
    key = raw.strip().lower()
    return _NEWSLETTER_CANONICAL.get(key, raw.strip())

def _parse_date(raw: str):
    val = raw.strip()
    if not val or val.lower() == "unknown":
        return None, False
    try:
        dt = datetime.strptime(val, "%d-%m-%Y")
        return dt.date(), True
    except ValueError:
        return None, False

def _split_personas(raw: str) -> list[str]:
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
    if not raw or not raw.strip():
        return []
    parts = raw.split(",")
    nls = []
    for p in parts:
        p = p.strip()
        if p:
            nls.append(_normalize_newsletter(p))
    return nls

def _normalize_row(r):
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

def load_secrets():
    secrets_path = Path(".streamlit") / "secrets.toml"
    if not secrets_path.exists():
        raise FileNotFoundError("Secrets file .streamlit/secrets.toml not found.")
    
    secrets = {}
    current_section = None
    with open(secrets_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].strip()
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if current_section:
                    if current_section not in secrets:
                        secrets[current_section] = {}
                    secrets[current_section][key] = val
                else:
                    secrets[key] = val
    return secrets

def main():
    print("Starting sync to MotherDuck...")
    try:
        # Load credentials
        secrets = load_secrets()
        if "motherduck" not in secrets:
            raise KeyError("Missing [motherduck] section in secrets.toml")
        
        token = secrets["motherduck"].get("token")
        database = secrets["motherduck"].get("database")
        
        if not token:
            raise ValueError("Missing 'token' under [motherduck] section in secrets.toml")
        if not database or database == "YOUR DATBASE HERE":
            raise ValueError("Please configure a valid database name in secrets.toml before running the sync script.")
            
        print(f"Connecting to MotherDuck database: '{database}'...")
        os.environ["motherduck_token"] = token
        con = duckdb.connect(f"md:{database}")
        
        # Read local JSONL data
        if not JSONL_PATH.exists():
            raise FileNotFoundError(f"Local JSONL database file not found at {JSONL_PATH}")
            
        print(f"Reading local JSONL data from {JSONL_PATH}...")
        jsonl_rows = []
        with open(JSONL_PATH, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    if "s_no" not in row or row["s_no"] is None:
                        raise KeyError("Missing 's_no' field")
                    # Check other fields
                    required_fields = [
                        "source_newsletter", "date_of_appearance", "content_type",
                        "theme", "extracted_content", "sponsored_content",
                        "target_persona", "estimated_setup_time"
                    ]
                    for field in required_fields:
                        if field not in row:
                            raise KeyError(f"Missing field '{field}'")
                    
                    jsonl_rows.append(_normalize_row(row))
                except Exception as e:
                    print(f"Warning: Skipping line {line_num} due to parsing error: {e}")
        
        if not jsonl_rows:
            print("No valid rows found in JSONL. Aborting sync.")
            return

        print(f"Parsed {len(jsonl_rows)} valid entries. Preparing database table...")
        
        # Create schema and table on MotherDuck
        con.execute("DROP TABLE IF EXISTS entries;")
        con.execute("""
            CREATE TABLE entries (
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
            );
        """)
        
        # Load using pandas
        df = pd.DataFrame(jsonl_rows)
        
        # Insert data
        print("Uploading data to MotherDuck...")
        con.execute("INSERT INTO entries SELECT * FROM df;")
        
        # Build FTS index on MotherDuck
        print("Building FTS index on MotherDuck...")
        con.execute("INSTALL fts;")
        con.execute("LOAD fts;")
        con.execute("""
            PRAGMA create_fts_index(
                'entries',
                'sno',
                'extracted_content', 'theme', 'content_type', 'source_newsletter_text',
                overwrite = 1
            );
        """)
        
        # Verify row count
        count = con.execute("SELECT COUNT(*) FROM entries;").fetchone()[0]
        print(f"SUCCESS: Synced {count} rows to MotherDuck table 'entries' successfully.")
        
    except Exception as e:
        print(f"FAILURE: Sync to MotherDuck failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
