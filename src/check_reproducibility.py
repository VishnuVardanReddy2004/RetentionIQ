
import hashlib
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "retentioniq.db"


def database_checksum():
    digest = hashlib.sha256()

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

            rows = connection.execute(
                f'SELECT * FROM "{table}" ORDER BY 1'
            ).fetchall()

            for row in rows:
                digest.update(repr(row).encode("utf-8"))

    return digest.hexdigest()


if __name__ == "__main__":
    print("Database SHA-256:")
    print(database_checksum())
