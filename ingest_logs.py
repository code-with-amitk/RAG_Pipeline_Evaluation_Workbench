"""
ingest_logs.py
Parses firewall.log and vpn.log and loads them into a SQLite database (logs.db).
Tables created:
  - firewall_events(id, timestamp, event_type, src_ip, dst_ip, policy)
  - vpn_events(id, timestamp, event_type, username, ip)
"""

import sqlite3
import re
import os

LOGS_DIR = "./logs"
DB_PATH = "./logs.db"

# ── Regex patterns matching the log formats ──────────────────────────────────
FIREWALL_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<event_type>FIREWALL_\w+)\s+"
    r"src=(?P<src_ip>[\d.]+)\s+"
    r"dst=(?P<dst_ip>[\d.]+)\s+"
    r"policy=(?P<policy>\w+)"
)

VPN_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<event_type>VPN_\w+)\s+"
    r"user=(?P<username>[\w.]+)\s+"
    r"ip=(?P<ip>[\d.]+)"
)


def create_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS firewall_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            src_ip    TEXT NOT NULL,
            dst_ip    TEXT NOT NULL,
            policy    TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vpn_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            username  TEXT NOT NULL,
            ip        TEXT NOT NULL
        )
    """)


def ingest_firewall(cursor, filepath):
    inserted = 0
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = FIREWALL_PATTERN.match(line)
            if match:
                cursor.execute(
                    "INSERT INTO firewall_events (timestamp, event_type, src_ip, dst_ip, policy) VALUES (?, ?, ?, ?, ?)",
                    (match["timestamp"], match["event_type"], match["src_ip"], match["dst_ip"], match["policy"])
                )
                inserted += 1
            else:
                print(f"  [WARN] Could not parse firewall line: {line}")
    return inserted


def ingest_vpn(cursor, filepath):
    inserted = 0
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = VPN_PATTERN.match(line)
            if match:
                cursor.execute(
                    "INSERT INTO vpn_events (timestamp, event_type, username, ip) VALUES (?, ?, ?, ?)",
                    (match["timestamp"], match["event_type"], match["username"], match["ip"])
                )
                inserted += 1
            else:
                print(f"  [WARN] Could not parse VPN line: {line}")
    return inserted


def main():
    # Remove old DB so we start fresh on each run
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    create_tables(cursor)

    fw_count = ingest_firewall(cursor, os.path.join(LOGS_DIR, "firewall.log"))
    vpn_count = ingest_vpn(cursor, os.path.join(LOGS_DIR, "vpn.log"))

    conn.commit()
    conn.close()

    print(f"Ingestion complete.")
    print(f"  firewall_events : {fw_count} rows inserted")
    print(f"  vpn_events      : {vpn_count} rows inserted")
    print(f"  Database saved  : {DB_PATH}")


if __name__ == "__main__":
    main()
