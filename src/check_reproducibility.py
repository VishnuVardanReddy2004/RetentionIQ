
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "retentioniq.db"


def database_fingerprint():
    """Return stable row counts and a content checksum."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    digest = hashlib.sha256()
    row_counts = {}

    with sqlite3.connect(DB_PATH) as connection:
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        for (table,) in tables:
            digest.update(table.encode("utf-8"))

            # Quote table names safely for SQLite.
            quoted_table = '"' + table.replace('"', '""') + '"'
            rows = connection.execute(
                f"SELECT * FROM {quoted_table} ORDER BY 1"
            ).fetchall()

            row_counts[table] = len(rows)

            for row in rows:
                canonical_row = json.dumps(
                    row,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    default=str,
                )
                digest.update(canonical_row.encode("utf-8"))
                digest.update(b"\n")

    return row_counts, digest.hexdigest()


def main():
    try:
        counts_first, hash_first = database_fingerprint()
        counts_second, hash_second = database_fingerprint()
    except (OSError, sqlite3.Error) as error:
        print(f"ERROR: {error}")
        sys.exit(1)

    print("RETENTIONIQ REPRODUCIBILITY CHECK")
    print("=" * 40)
    print("\nTable row counts:")
    for table, count in counts_first.items():
        print(f"{table}: {count:,}")

    print(f"\nFirst checksum:  {hash_first}")
    print(f"Second checksum: {hash_second}")

    if counts_first == counts_second and hash_first == hash_second:
        print("\nPASS: Repeated reads of the current database match.")
        print("NOTE: This does not prove two independent data generations match.")
    else:
        print("\nFAIL: Database fingerprints differ.")
        sys.exit(1)


if __name__ == "__main__":
    main()
