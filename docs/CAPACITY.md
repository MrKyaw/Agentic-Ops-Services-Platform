# Capacity model (DL-4; thresholds, quarterly review)

Design capacity (PRD 12-month): 500 concurrent runs, 100 rps gateway, 50M chunks, 20M graph nodes.

| Resource | Scale threshold | Action |
|---|---|---|
| pgvector chunks | 10M per index | partition by kb + read replica |
| Neo4j nodes | 5M | dedicated cluster sizing review |
| API latency P95 | 2 s sustained | add replicas (stateless services scale horizontally) |
| Queue depth (ingestion) | 1k pending | scale workers, backpressure to clients |
| Token spend/day/tenant | quota 80% | alert tenant admin; hard cap at 100% |

Current scale: single digits. Load proof at 2x design capacity requires staging (NF-S3 pending).
