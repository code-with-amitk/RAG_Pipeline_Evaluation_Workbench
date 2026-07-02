# RAGAS (Retrieval Augmented Generation Assessment)

[What is RAGAS](https://code-with-amitk.github.io/Machine%20Learning/)

file : evaluate.py

## Code Walk
1. Enter virtual env

2. Create command line parser, which can take following arguments
```
evaluate.py     
    --top-k (default 3) //Retrieval depth
    --limit (default None)      //Evaluate only first N questions
    --use-cache (default )  //Reuse cached RAG responses from rag_responses.json
    --ragas-only   ()   //Skip RAG queries; score cached responses with RAGAS only
    --max-workers   (default 2)  //RAGAS parallel workers 
    --output (default evaluation_results.csv)   //Output CSV path
```

3. Load questions from [benchmark_qa.json](../benchmark_qa.json)

4. Create RAGAS infra to test RAG
```
// 1. Create LLM Client for ragas
ragas_llm_client = OpenAI(api_key=api_key, base_url=base_url)

// 2. Create embeddings
ragas_langchain_embeddings = LangchainOpenAIEmbeddings(..)

// 3. Wrap LLM client into llm factory
llm = llm_factory("gpt-4o-mini", client=ragas_llm_client)

// 4. Configuration for RAGAS
// max_workers: how many concurrent threads are used for parallel tasks
// max_retries: how many times the system should attempt to call the API
// max_wait: maximum time the system should wait between retries or for an API response before marking the task as failed.
run_config = RunConfig(max_workers=max_workers, max_retries=5, max_wait=120)

// 5. Evaluate RAG pipeline
from ragas import evaluate
ragas_result = evaluate(
  dataset = rag_response,
  metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
  llm=ragas_llm,
  embeddings=ragas_embeddings,
  run_config=ragas_run_config,
  raise_exceptions=False,
)
```

6. RAGAS results in csv(table) format in file [evaluate_results.csv](../evaluation_results.csv)

| id | question | ground_truth | answer | difficulty | category | faithfulness | answer_relevancy | context_precision | context_recall |
|---:|---|---|---|---|---|---:|---:|---:|---:|
| 1 | What destination IP was blocked when source 10.1.1.5 attempted outbound traffic at 2025-05-01 08:02:11? | 8.8.8.8. The firewall log shows: 2025-05-01 08:02:11 FIREWALL_DENY src=10.1.1.5 dst=8.8.8.8 policy=OUTBOUND_BLOCK. | The destination IP that was blocked when source 10.1.1.5 attempted outbound traffic at the specified time was 8.8.8.8. | easy | single-event lookup | 1.0 | 0.9458696091251101 | 0.9999999999 | 1.0 |
| 2 | Which user had a successful VPN login at 2025-05-01 08:10:30? | alice.smith logged in successfully from IP 192.168.1.50 at 2025-05-01 08:10:30. | The user who had a successful VPN login at 2025-05-01 08:10:30 is alice.smith. | easy | single-event lookup | 1.0 | 0.9453676604847042 | 0.9999999999 | 1.0 |
| 3 | What firewall policy was triggered for source IP 172.16.0.4 at 2025-05-01 08:31:55? | PORT_SCAN_DETECTED. The event blocked traffic from 172.16.0.4 to destination 45.33.32.156. | The firewall policy triggered for source IP 172.16.0.4 at 2025-05-01 08:31:55 was PORT_SCAN_DETECTED. | easy | single-event lookup | 1.0 | 0.8869908558685444 | 0.99999999995 | 1.0 |
| 4 | From which IP address did john.doe attempt VPN login at 2025-05-01 08:01:05? | 185.22.11.4. The log entry reads: 2025-05-01 08:01:05 VPN_LOGIN_FAILED user=john.doe ip=185.22.11.4. | 185.22.11.4 | easy | single-event lookup | 1.0 | 0.37588347900692004 | 0.9999999999 | 1.0 |
| 5 | How many total FIREWALL_DENY events are recorded in the firewall log? | 28 FIREWALL_DENY events are recorded in firewall.log. | There are a total of 40 FIREWALL_DENY events recorded in the firewall log. | easy | aggregation | 0.0 | 0.9765830775873535 | 0.9999999999 | 0.0 |
| 6 | What are the three distinct firewall policy types in the logs? | OUTBOUND_BLOCK (15 events), INBOUND_BLOCK (8 events), and PORT_SCAN_DETECTED (5 events). | The three distinct firewall policy types in the logs are INBOUND_BLOCK, OUTBOUND_BLOCK, and PORT_SCAN_DETECTED. | medium | aggregation | 0.0 | 0.999999645373078 | 0.99999999995 | 1.0 |
| 7 | How many OUTBOUND_BLOCK firewall events does source IP 10.1.1.5 have? | 5 OUTBOUND_BLOCK events originate from source IP 10.1.1.5. | Source IP 10.1.1.5 has 4 OUTBOUND_BLOCK firewall events. | medium | aggregation | 1.0 | 0.9622712969038728 | 0.99999999995 | 1.0 |
| 8 | How many VPN login failures did user john.doe have? | john.doe had 7 VPN_LOGIN_FAILED events, all from IP 185.22.11.4. | User john.doe had a total of 6 VPN login failures. | medium | aggregation | 1.0 | 0.9999996053346408 | 0.9999999999 | 1.0 |
| 9 | How many OUTBOUND_BLOCK firewall events occurred between 08:00 and 09:00 on 2025-05-01? | 5 OUTBOUND_BLOCK events occurred in that hour (at 08:02:11, 08:05:33, 08:11:47, 08:22:19, and 08:45:08). | There were 5 OUTBOUND_BLOCK firewall events that occurred between 08:00 and 09:00 on 2025-05-01. | medium | time-window queries | 0.5 | 0.9999999999999998 | 0.9999999999 | 1.0 |
| 10 | How many VPN events of any type occurred between 10:00 and 11:00 on 2025-05-01? | 5 VPN events occurred in that hour (at 10:05:49, 10:18:22, 10:31:07, 10:44:55, and 10:58:30). | There were 8 VPN events of any type that occurred between 10:00 and 11:00 on 2025-05-01. | medium | time-window queries | 0.0 | 0.9893048646488724 | 0.9999999999 | 0.0 |
| 11 | Did john.doe experience three VPN login failures within a 10-minute window around 08:01 on 2025-05-01? | Yes. john.doe failed at 08:01:05, 08:03:44, and 08:06:12 — all within a 5-minute window. | Yes, john.doe experienced three VPN login failures within a 10-minute window around 08:01 on 2025-05-01. The failures occurred at 08:01:05, 08:03:44, and 08:06:12. | hard | time-window queries | 1.0 | 0.8695841810591061 | 0.9999999999 | 1.0 |
| 12 | Which IP addresses appear in both VPN login failures and firewall deny events? | Three IPs appear in both logs: 185.22.11.4 (7 VPN failures, 4 firewall blocks), 203.0.113.7 (7 VPN failures, 1 firewall block), and 172.16.0.4 (4 VPN failures, 3 firewall blocks). | The IP address that appears in both VPN login failures and firewall deny events is 185.22.11.4. | hard | cross-log correlation | 1.0 | 0.9218554283082063 | 0.9999999999 | 1.0 |
| 13 | How many VPN failures and firewall events are associated with IP 185.22.11.4? | IP 185.22.11.4 is linked to 7 VPN login failures (user john.doe) and 4 firewall INBOUND_BLOCK events as the source IP. | There are 6 VPN failures associated with IP 185.22.11.4. Additionally, there are 4 firewall events related to the same IP. | hard | cross-log correlation | 0.5 | 0.9999999999999999 | 0.0 | 1.0 |
| 14 | Which VPN user is associated with the IP address that triggered PORT_SCAN_DETECTED firewall events? | mallory.x. That user had 4 VPN login failures from IP 172.16.0.4, which is also the source IP in 3 PORT_SCAN_DETECTED firewall events. | The VPN user associated with the IP address that triggered PORT_SCAN_DETECTED firewall events is mallory.x, who used the IP address 172.16.0.4. | medium | cross-log correlation | 1.0 | 0.9774701044340874 | 0.5833333333041666 | 0.3333333333333333 |
| 15 | Is IP 203.0.113.7 involved in both VPN failures and firewall blocks? | Yes. eve.hacker had 7 VPN login failures from 203.0.113.7, and the firewall denied inbound traffic from 203.0.113.7 to 10.1.1.5 at 11:03:58 under policy INBOUND_BLOCK. | Yes, the IP 203.0.113.7 is involved in both VPN login failures and firewall blocks. It appears multiple times in the VPN log with failed login attempts and is also listed in the firewall log with denied inbound connections. | hard | cross-log correlation | 1.0 | 0.8538740935072114 | 0.49999999995 | 1.0 |