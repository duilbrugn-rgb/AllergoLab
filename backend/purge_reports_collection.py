"""
Administrative helper for leftover MongoDB `reports` documents.

Default mode is dry-run: prints the document count and does not delete.
Deletion happens only with --execute.

This script is never invoked by the application runtime.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")


def connect():
    mongo_url = os.environ.get("MONGO_URL")
    db_name = os.environ.get("DB_NAME")
    if not mongo_url or not db_name:
        raise SystemExit("MONGO_URL and DB_NAME must be set in the environment or backend/.env")
    client = MongoClient(mongo_url)
    return client, client[db_name]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inspect or delete leftover documents in the reports collection."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete all documents in the reports collection. Default is dry-run.",
    )
    args = parser.parse_args(argv)

    client, db = connect()
    try:
        count = db.reports.count_documents({})
        print(f"reports collection document count: {count}")
        if not args.execute:
            print("Dry-run only. Re-run with --execute to delete these documents.")
            return 0
        result = db.reports.delete_many({})
        print(f"Deleted {result.deleted_count} documents from reports.")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
