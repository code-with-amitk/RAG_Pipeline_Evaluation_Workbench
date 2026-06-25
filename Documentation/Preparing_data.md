## Preparing data to feed pipeline

### DB File
#### Creating [ingest_logs.py](../ingest_logs.py)
- [logs.db](../logs.db) is created from [VPN Logs](../logs/vpn.log) & [Firewall Logs](../logs/firewall.log) by script called [injest logs](../ingest_logs.py)
- This script reads the pattern from log files, create these tables(firewall_events, vpn_events) and then inserts the data into these tables after reading from log files.
```
CREATE TABLE IF NOT EXISTS firewall_events
CREATE TABLE IF NOT EXISTS vpn_events 

INSERT INTO firewall_events 
INSERT INTO vpn_events
```

#### Checking using pandas [sql_analysis](../sql_analysis.py)
- Read sql database using pandas read_sql_query() which executes the SQL query passed to and returns a [pandas dataframe](https://code-with-amitk.github.io/Machine%20Learning/Libraries/Pandas/Introduction.html)
- Perform different queries on logs.db using pandas read_sql_query()
