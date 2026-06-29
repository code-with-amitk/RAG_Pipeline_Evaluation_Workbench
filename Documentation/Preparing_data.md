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


### Benchmark question Preparation [benchmark_qq.json](../benchmark_qa.json)
- Create set of 25 questions (8 easy, 9 medium, 8 hard)
- Categorize questions as

-- Single-event lookup — e.g. destination IP blocked at a specific timestamp
-- Aggregation — e.g. total firewall events (28), top source IPs
-- Time-window — e.g. john.doe’s 3 failures within 5 minutes around 08:01
-- Cross-log correlation — e.g. IPs appearing in both VPN failures and firewall blocks (185.22.11.4, 203.0.113.7, 172.16.0.4)

- Here a question is asked from LLM, ground_truth is correct answer. 

-- This is a easy question, where this firewall logs can provide the answer `2025-05-01 08:02:11 FIREWALL_DENY src=10.1.1.5 dst=8.8.8.8 policy=OUTBOUND_BLOCK`
```json
{
    "id": 1,
    "question": "What destination IP was blocked when source 10.1.1.5 attempted outbound traffic at 2025-05-01 08:02:11?",
    "ground_truth": "8.8.8.8. The firewall log shows: 2025-05-01 08:02:11 FIREWALL_DENY src=10.1.1.5 dst=8.8.8.8 policy=OUTBOUND_BLOCK.",
    "difficulty": "easy",
    "category": "single-event lookup"
},
```
-- This is a hasrd question. Where answer can be derived by looking at 2 or more log entries.
```json
{
    "id": 25,
    "question": "What are the top 3 source IPs by total firewall deny count across all policy types?",
    "ground_truth": "10.1.1.6 and 10.1.1.5 are tied for first with 5 events each, followed by 185.22.11.4 with 4 events.",
    "difficulty": "hard",
    "category": "aggregation"
}
```