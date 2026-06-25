"""
sql_analysis.py
Runs 4 SQL analytical queries against logs.db and loads results into Pandas DataFrames.
Covers:
  Q1. Count of events grouped by event type (both tables)
  Q2. Top 5 source IPs with the most blocked outbound traffic
  Q3. Users with VPN login failures within a 10-minute window
  Q4. Cross-table: IPs that appear in both VPN failures and firewall blocks
"""

import sqlite3
import pandas as pd

DB_PATH = "./logs.db"


def run_query(conn, title, sql):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    # pandas.read_sql_query(sql, con, index_col=None, coerce_float=True, 
    #                       params=None, parse_dates=None, chunksize=None, 
    #                       dtype=None, dtype_backend=<no_default>)
    # Returns a DataFrame corresponding SQL query result.
    df = pd.read_sql_query(sql, conn)
    print("run_query: \n", df.to_string(index=False))
    print(f"\n  rows: {len(df)}  |  columns: {list(df.columns)}")
    return df


def main():
    conn = sqlite3.connect(DB_PATH)

    # ── Q1: Count of events grouped by event type (firewall) ─────────────────
    df_fw_types = run_query(conn, "Q1a: Firewall — Event count by type", """
        SELECT event_type,
               COUNT(*) AS total_events
        FROM   firewall_events
        GROUP  BY event_type
        ORDER  BY total_events DESC
    """)

    # Count of events grouped by event type (vpn)
    df_vpn_types = run_query(conn, "Q1b: VPN — Event count by type", """
        SELECT event_type,
               COUNT(*) AS total_events
        FROM   vpn_events
        GROUP  BY event_type
        ORDER  BY total_events DESC
    """)

    # ── Q2: Top 5 source IPs with the most blocked outbound traffic ───────────
    df_top_ips = run_query(conn, "Q2: Top 5 source IPs — blocked outbound traffic", """
        SELECT src_ip,
               COUNT(*) AS block_count
        FROM   firewall_events
        WHERE  policy = 'OUTBOUND_BLOCK'
        GROUP  BY src_ip
        ORDER  BY block_count DESC
        LIMIT  5
    """)

    # ── Q3: Users with VPN failures within any 10-minute window ──────────────
    # Self-join: find pairs of failures for the same user within 600 seconds
    df_window_failures = run_query(conn, "Q3: Users with VPN failures within a 10-minute window", """
        SELECT DISTINCT a.username,
               a.timestamp AS failure_1,
               b.timestamp AS failure_2,
               ROUND((JULIANDAY(b.timestamp) - JULIANDAY(a.timestamp)) * 24 * 60, 2) AS minutes_apart
        FROM   vpn_events a
        JOIN   vpn_events b
               ON  a.username  = b.username
               AND a.id        < b.id
               AND a.event_type = 'VPN_LOGIN_FAILED'
               AND b.event_type = 'VPN_LOGIN_FAILED'
               AND (JULIANDAY(b.timestamp) - JULIANDAY(a.timestamp)) * 24 * 60 <= 10
        ORDER  BY a.username, a.timestamp
    """)

    # ── Q4: IPs appearing in BOTH VPN failures AND firewall blocks ────────────
    df_crossjoin = run_query(conn, "Q4: IPs in both VPN failures and firewall blocks (cross-table correlation)", """
        SELECT v.ip,
               COUNT(DISTINCT v.id) AS vpn_failures,
               COUNT(DISTINCT f.id) AS firewall_blocks
        FROM   vpn_events v
        JOIN   firewall_events f
               ON  v.ip = f.src_ip
               OR  v.ip = f.dst_ip
        WHERE  v.event_type = 'VPN_LOGIN_FAILED'
        GROUP  BY v.ip
        ORDER  BY vpn_failures DESC
    """)

    conn.close()

    # ── Summary stats on numeric columns ─────────────────────────────────────
    print(f"\n{'='*60}")
    print("  Summary Stats: Firewall block count per source IP")
    print(f"{'='*60}")
    fw_per_ip = pd.read_sql_query("""
        SELECT src_ip, COUNT(*) AS block_count
        FROM firewall_events GROUP BY src_ip
    """, sqlite3.connect(DB_PATH))
    print(fw_per_ip["block_count"].describe().to_string())

    print(f"\n{'='*60}")
    print("  Summary Stats: VPN failure count per user")
    print(f"{'='*60}")
    vpn_per_user = pd.read_sql_query("""
        SELECT username, COUNT(*) AS failure_count
        FROM vpn_events
        WHERE event_type = 'VPN_LOGIN_FAILED'
        GROUP BY username
    """, sqlite3.connect(DB_PATH))
    print(vpn_per_user.to_string(index=False))


if __name__ == "__main__":
    main()
