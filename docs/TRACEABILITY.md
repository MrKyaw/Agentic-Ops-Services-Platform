# TRACEABILITY.md

Source: `Agentic-Ops-Services-Platform_PRD.md` Draft v1.0. Phase A — code/test columns are TBD (Not started). Coverage: every extracted requirement ID has a row.

Total requirement rows: 202 (functional + non-functional; PRD carries no separate `AI-NNN` IDs — AI behaviors tracked via AO/PI/RG/FT/TS/EV rows).

| Req ID | PRD section | Design element | Code module (target) | Test case IDs (target) | Status |
|---|---|---|---|---|---|
| AO-1 | 9.2 | orchestrator | `orchestrator` | T-AO-1 | Partial (Phase 1 backend) |
| AO-10 | 9.2 | orchestrator | `orchestrator` | T-AO-10 | Partial (Phase 1 full-stack) |
| AO-11 | 9.2 | orchestrator | `orchestrator` | T-AO-11 | Partial (Phase 1 backend) |
| AO-12 | 9.2 | orchestrator | `orchestrator` | T-AO-12 | Partial (Phase 1 full-stack) |
| AO-13 | 9.2 | orchestrator | `orchestrator` | T-AO-13 | Partial (Phase 1 full-stack) |
| AO-14 | 9.2 | orchestrator | `orchestrator` | T-AO-14 | Not started |
| AO-15 | 9.2 | orchestrator | `orchestrator` | T-AO-15 | Partial (Phase 1 backend) |
| AO-16 | 9.2 | orchestrator | `orchestrator` | T-AO-16 | Partial (Phase 1 backend) |
| AO-17 | 9.2 | orchestrator | `orchestrator` | T-AO-17 | Partial (Phase 1 full-stack) |
| AO-18 | 9.2 | orchestrator | `orchestrator` | T-AO-18 | Not started |
| AO-2 | 9.2 | orchestrator | `orchestrator` | T-AO-2 | Partial (Phase 1 backend) |
| AO-3 | 9.2 | orchestrator | `orchestrator` | T-AO-3 | Partial (Phase 1 full-stack) |
| AO-4 | 9.2 | orchestrator | `orchestrator` | T-AO-4 | Not started |
| AO-5 | 9.2 | orchestrator | `orchestrator` | T-AO-5 | Partial (Phase 1 backend) |
| AO-6 | 9.2 | orchestrator | `orchestrator` | T-AO-6 | Partial (Phase 1 backend) |
| AO-7 | 9.2 | orchestrator | `orchestrator` | T-AO-7 | Partial (Phase 1 backend) |
| AO-8 | 9.2 | orchestrator | `orchestrator` | T-AO-8 | Partial (Phase 1 backend) |
| AO-9 | 9.2 | orchestrator | `orchestrator` | T-AO-9 | Partial (Phase 1 backend) |
| AP-1 | 9.10 | api-gateway + bff | `api-gateway` | T-AP-1 | Partial (Phase 0 skeleton) |
| AP-2 | 9.10 | api-gateway + bff | `api-gateway` | T-AP-2 | Partial (Phase 0 skeleton) |
| AP-3 | 9.10 | api-gateway + bff | `api-gateway` | T-AP-3 | Partial (Phase 0 skeleton) |
| AP-4 | 9.10 | api-gateway + bff | `api-gateway` | T-AP-4 | Partial (Phase 0 skeleton) |
| AP-5 | 9.10 | api-gateway + bff | `api-gateway` | T-AP-5 | Not started |
| AP-6 | 9.10 | api-gateway + bff | `api-gateway` | T-AP-6 | Not started |
| AP-7 | 9.10 | api-gateway + bff | `api-gateway` | T-AP-7 | Not started |
| AP-8 | 9.10 | api-gateway + bff | `api-gateway` | T-AP-8 | Not started |
| BE-1 | 9.9.2 | backend (fastapi) + sdk | `backend` | T-BE-1 | Partial (Phase 1 backend) |
| BE-2 | 9.9.2 | backend (fastapi) + sdk | `backend` | T-BE-2 | Partial (Phase 1 backend) |
| BE-3 | 9.9.2 | backend (fastapi) + sdk | `backend` | T-BE-3 | Not started |
| BE-4 | 9.9.2 | backend (fastapi) + sdk | `backend` | T-BE-4 | Partial (Phase 1 backend) |
| BE-5 | 9.9.2 | backend (fastapi) + sdk | `backend` | T-BE-5 | Not started |
| BE-6 | 9.9.2 | backend (fastapi) + sdk | `backend` | T-BE-6 | Partial (Phase 1 backend) |
| BE-7 | 9.9.2 | backend (fastapi) + sdk | `backend` | T-BE-7 | Partial (Phase 1 backend) |
| CP-1 | 11.3 | governance-service | `governance-service` | T-CP-1 | Partial (Phase 1 full-stack) |
| CP-2 | 11.3 | governance-service | `governance-service` | T-CP-2 | Not started |
| CP-3 | 11.3 | governance-service | `governance-service` | T-CP-3 | Partial (Phase 1 full-stack) |
| CP-4 | 11.3 | governance-service | `governance-service` | T-CP-4 | Not started |
| CP-5 | 11.3 | governance-service | `governance-service` | T-CP-5 | Not started |
| CP-6 | 11.3 | governance-service | `governance-service` | T-CP-6 | Not started |
| DG-1 | 16 | data-governance | `data-governance` | T-DG-1 | Not started |
| DG-2 | 16 | data-governance | `data-governance` | T-DG-2 | Partial (Phase 1 full-stack) |
| DG-3 | 16 | data-governance | `data-governance` | T-DG-3 | Not started |
| DG-4 | 16 | data-governance | `data-governance` | T-DG-4 | Not started |
| DG-5 | 16 | data-governance | `data-governance` | T-DG-5 | Partial (Phase 1 backend) |
| DG-6 | 16 | data-governance | `data-governance` | T-DG-6 | Not started |
| DL-1 | 9.6 | data-layer (postgres/pgvector, neo4j, s3) | `data-layer` | T-DL-1 | Partial (Phase 1 backend) |
| DL-2 | 9.6 | data-layer (postgres/pgvector, neo4j, s3) | `data-layer` | T-DL-2 | Partial (Phase 1 full-stack) |
| DL-3 | 9.6 | data-layer (postgres/pgvector, neo4j, s3) | `data-layer` | T-DL-3 | Not started |
| DL-4 | 9.6 | data-layer (postgres/pgvector, neo4j, s3) | `data-layer` | T-DL-4 | Not started |
| DL-5 | 9.6 | data-layer (postgres/pgvector, neo4j, s3) | `data-layer` | T-DL-5 | Not started |
| DL-6 | 9.6 | data-layer (postgres/pgvector, neo4j, s3) | `data-layer` | T-DL-6 | Partial (Phase 1 backend) |
| DL-7 | 9.6 | data-layer (postgres/pgvector, neo4j, s3) | `data-layer` | T-DL-7 | Partial (Phase 1 backend) |
| DL-8 | 9.6 | data-layer (postgres/pgvector, neo4j, s3) | `data-layer` | T-DL-8 | Partial (Phase 1 backend) |
| DL-9 | 9.6 | data-layer (postgres/pgvector, neo4j, s3) | `data-layer` | T-DL-9 | Not started |
| ET-1 | 9.8 | experiment-service + dashboards | `experiment-service` | T-ET-1 | Not started |
| ET-2 | 9.8 | experiment-service + dashboards | `experiment-service` | T-ET-2 | Not started |
| ET-3 | 9.8 | experiment-service + dashboards | `experiment-service` | T-ET-3 | Not started |
| ET-4 | 9.8 | experiment-service + dashboards | `experiment-service` | T-ET-4 | Not started |
| ET-5 | 9.8 | experiment-service + dashboards | `experiment-service` | T-ET-5 | Not started |
| ET-6 | 9.8 | experiment-service + dashboards | `experiment-service` | T-ET-6 | Not started |
| ET-7 | 9.8 | experiment-service + dashboards | `experiment-service` | T-ET-7 | Not started |
| ET-8 | 9.8 | experiment-service + dashboards | `experiment-service` | T-ET-8 | Not started |
| EV-1 | 9.12 | eval-harness | `eval-harness` | T-EV-1 | Partial (Phase 0 skeleton) |
| EV-2 | 9.12 | eval-harness | `eval-harness` | T-EV-2 | Not started |
| EV-3 | 9.12 | eval-harness | `eval-harness` | T-EV-3 | Partial (Phase 1 backend) |
| EV-4 | 9.12 | eval-harness | `eval-harness` | T-EV-4 | Partial (Phase 1 backend) |
| EV-5 | 9.12 | eval-harness | `eval-harness` | T-EV-5 | Not started |
| EV-6 | 9.12 | eval-harness | `eval-harness` | T-EV-6 | Partial (Phase 1 backend) |
| EV-7 | 9.12 | eval-harness | `eval-harness` | T-EV-7 | Not started |
| EV-8 | 9.12 | eval-harness | `eval-harness` | T-EV-8 | Not started |
| FE-1 | 9.9.1 | frontend (angular) | `frontend` | T-FE-1 | Partial (Phase 1 full-stack) |
| FE-10 | 9.9.1 | frontend (angular) | `frontend` | T-FE-10 | Partial (Phase 1 full-stack) |
| FE-2 | 9.9.1 | frontend (angular) | `frontend` | T-FE-2 | Partial (Phase 1 full-stack) |
| FE-3 | 9.9.1 | frontend (angular) | `frontend` | T-FE-3 | Partial (Phase 1 full-stack) |
| FE-4 | 9.9.1 | frontend (angular) | `frontend` | T-FE-4 | Partial (Phase 1 full-stack) |
| FE-5 | 9.9.1 | frontend (angular) | `frontend` | T-FE-5 | Partial (Phase 1 full-stack) |
| FE-6 | 9.9.1 | frontend (angular) | `frontend` | T-FE-6 | Partial (Phase 1 full-stack) |
| FE-7 | 9.9.1 | frontend (angular) | `frontend` | T-FE-7 | Not started |
| FE-8 | 9.9.1 | frontend (angular) | `frontend` | T-FE-8 | Not started |
| FE-9 | 9.9.1 | frontend (angular) | `frontend` | T-FE-9 | Partial (Phase 1 full-stack) |
| FT-1 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-1 | Not started |
| FT-10 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-10 | Not started |
| FT-11 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-11 | Not started |
| FT-12 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-12 | Not started |
| FT-13 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-13 | Not started |
| FT-2 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-2 | Not started |
| FT-3 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-3 | Not started |
| FT-4 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-4 | Not started |
| FT-5 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-5 | Not started |
| FT-6 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-6 | Not started |
| FT-7 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-7 | Not started |
| FT-8 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-8 | Not started |
| FT-9 | 9.7 | finetune-service + model-registry | `finetune-service` | T-FT-9 | Not started |
| IN-1 | 13 | infra (terraform/eks) | `infra` | T-IN-1 | Partial (Phase 0 skeleton) |
| IN-2 | 13 | infra (terraform/eks) | `infra` | T-IN-2 | Not started |
| IN-3 | 13 | infra (terraform/eks) | `infra` | T-IN-3 | Not started |
| IN-4 | 13 | infra (terraform/eks) | `infra` | T-IN-4 | Not started |
| IN-5 | 13 | infra (terraform/eks) | `infra` | T-IN-5 | Not started |
| IN-6 | 13 | infra (terraform/eks) | `infra` | T-IN-6 | Not started |
| LO-1 | 14 | cicd + llmops | `cicd` | T-LO-1 | Partial (Phase 1 backend) |
| LO-2 | 14 | cicd + llmops | `cicd` | T-LO-2 | Not started |
| LO-3 | 14 | cicd + llmops | `cicd` | T-LO-3 | Not started |
| LO-4 | 14 | cicd + llmops | `cicd` | T-LO-4 | Not started |
| LO-5 | 14 | cicd + llmops | `cicd` | T-LO-5 | Not started |
| MC-1 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-1 | Partial (Phase 1 backend) |
| MC-10 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-10 | Not started |
| MC-11 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-11 | Partial (Phase 1 backend) |
| MC-12 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-12 | Not started |
| MC-13 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-13 | Partial (Phase 1 backend) |
| MC-14 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-14 | Not started |
| MC-15 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-15 | Partial (Phase 1 backend) |
| MC-2 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-2 | Partial (Phase 1 backend) |
| MC-3 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-3 | Partial (Phase 1 backend) |
| MC-4 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-4 | Partial (Phase 1 backend) |
| MC-5 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-5 | Partial (Phase 1 backend) |
| MC-6 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-6 | Partial (Phase 1 backend) |
| MC-7 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-7 | Partial (Phase 1 backend) |
| MC-8 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-8 | Partial (Phase 1 backend) |
| MC-9 | 9.4 | mcp-framework + mcp-registry | `mcp-framework` | T-MC-9 | Partial (Phase 1 backend) |
| MT-1 | 9.1 | tenant-service | `tenant-service` | T-MT-1 | Partial (Phase 0 skeleton) |
| MT-10 | 9.1 | tenant-service | `tenant-service` | T-MT-10 | Not started |
| MT-2 | 9.1 | tenant-service | `tenant-service` | T-MT-2 | Partial (Phase 0 skeleton) |
| MT-3 | 9.1 | tenant-service | `tenant-service` | T-MT-3 | Partial (Phase 0 skeleton) |
| MT-4 | 9.1 | tenant-service | `tenant-service` | T-MT-4 | Partial (Phase 1 full-stack) |
| MT-5 | 9.1 | tenant-service | `tenant-service` | T-MT-5 | Partial (Phase 1 full-stack) |
| MT-6 | 9.1 | tenant-service | `tenant-service` | T-MT-6 | Not started |
| MT-7 | 9.1 | tenant-service | `tenant-service` | T-MT-7 | Partial (Phase 0 skeleton) |
| MT-8 | 9.1 | tenant-service | `tenant-service` | T-MT-8 | Partial (Phase 1 full-stack) |
| MT-9 | 9.1 | tenant-service | `tenant-service` | T-MT-9 | Partial (Phase 0 skeleton) |
| OB-1 | 15.1 | observability | `observability` | T-OB-1 | Partial (Phase 1 backend) |
| OB-2 | 15.1 | observability | `observability` | T-OB-2 | Not started |
| OB-3 | 15.1 | observability | `observability` | T-OB-3 | Partial (Phase 1 backend) |
| OB-4 | 15.1 | observability | `observability` | T-OB-4 | Not started |
| OB-5 | 15.1 | observability | `observability` | T-OB-5 | Not started |
| OB-6 | 15.1 | observability | `observability` | T-OB-6 | Not started |
| OB-7 | 15.1 | observability | `observability` | T-OB-7 | Not started |
| OR-1 | 15.2 | ops runbooks | `ops` | T-OR-1 | Partial (Phase 1 backend) |
| OR-2 | 15.2 | ops runbooks | `ops` | T-OR-2 | Not started |
| OR-3 | 15.2 | ops runbooks | `ops` | T-OR-3 | Not started |
| OR-4 | 15.2 | ops runbooks | `ops` | T-OR-4 | Not started |
| OR-5 | 15.2 | ops runbooks | `ops` | T-OR-5 | Not started |
| OR-6 | 15.2 | ops runbooks | `ops` | T-OR-6 | Not started |
| PI-1 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-1 | Partial (Phase 1 backend) |
| PI-10 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-10 | Partial (Phase 1 backend) |
| PI-11 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-11 | Not started |
| PI-12 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-12 | Not started |
| PI-2 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-2 | Partial (Phase 1 backend) |
| PI-3 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-3 | Partial (Phase 1 backend) |
| PI-4 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-4 | Partial (Phase 1 backend) |
| PI-5 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-5 | Partial (Phase 1 backend) |
| PI-6 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-6 | Partial (Phase 1 backend) |
| PI-7 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-7 | Partial (Phase 1 backend) |
| PI-8 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-8 | Not started |
| PI-9 | 9.3 | intent-classifier + prompt-registry | `intent-classifier` | T-PI-9 | Not started |
| PV-1 | 11.2 | privacy-service | `privacy-service` | T-PV-1 | Not started |
| PV-2 | 11.2 | privacy-service | `privacy-service` | T-PV-2 | Not started |
| PV-3 | 11.2 | privacy-service | `privacy-service` | T-PV-3 | Not started |
| PV-4 | 11.2 | privacy-service | `privacy-service` | T-PV-4 | Partial (Phase 1 full-stack) |
| PV-5 | 11.2 | privacy-service | `privacy-service` | T-PV-5 | Not started |
| PV-6 | 11.2 | privacy-service | `privacy-service` | T-PV-6 | Not started |
| RG-1 | 9.5 | retrieval-service | `retrieval-service` | T-RG-1 | Partial (Phase 1 backend) |
| RG-10 | 9.5 | retrieval-service | `retrieval-service` | T-RG-10 | Partial (Phase 1 full-stack) |
| RG-11 | 9.5 | retrieval-service | `retrieval-service` | T-RG-11 | Partial (Phase 1 full-stack) |
| RG-12 | 9.5 | retrieval-service | `retrieval-service` | T-RG-12 | Partial (Phase 1 backend) |
| RG-13 | 9.5 | retrieval-service | `retrieval-service` | T-RG-13 | Not started |
| RG-14 | 9.5 | retrieval-service | `retrieval-service` | T-RG-14 | Partial (Phase 1 backend) |
| RG-15 | 9.5 | retrieval-service | `retrieval-service` | T-RG-15 | Partial (Phase 1 backend) |
| RG-16 | 9.5 | retrieval-service | `retrieval-service` | T-RG-16 | Partial (Phase 1 backend) |
| RG-17 | 9.5 | retrieval-service | `retrieval-service` | T-RG-17 | Partial (Phase 1 backend) |
| RG-2 | 9.5 | retrieval-service | `retrieval-service` | T-RG-2 | Partial (Phase 1 backend) |
| RG-3 | 9.5 | retrieval-service | `retrieval-service` | T-RG-3 | Partial (Phase 1 backend) |
| RG-4 | 9.5 | retrieval-service | `retrieval-service` | T-RG-4 | Partial (Phase 1 backend) |
| RG-5 | 9.5 | retrieval-service | `retrieval-service` | T-RG-5 | Partial (Phase 1 backend) |
| RG-6 | 9.5 | retrieval-service | `retrieval-service` | T-RG-6 | Not started |
| RG-7 | 9.5 | retrieval-service | `retrieval-service` | T-RG-7 | Partial (Phase 1 backend) |
| RG-8 | 9.5 | retrieval-service | `retrieval-service` | T-RG-8 | Partial (Phase 1 full-stack) |
| RG-9 | 9.5 | retrieval-service | `retrieval-service` | T-RG-9 | Not started |
| SC-1 | 11.1 | authn-authz + security | `authn-authz` | T-SC-1 | Partial (Phase 0 skeleton) |
| SC-10 | 11.1 | authn-authz + security | `authn-authz` | T-SC-10 | Not started |
| SC-2 | 11.1 | authn-authz + security | `authn-authz` | T-SC-2 | Partial (Phase 0 skeleton) |
| SC-3 | 11.1 | authn-authz + security | `authn-authz` | T-SC-3 | Not started |
| SC-4 | 11.1 | authn-authz + security | `authn-authz` | T-SC-4 | Partial (Phase 0 skeleton) |
| SC-5 | 11.1 | authn-authz + security | `authn-authz` | T-SC-5 | Not started |
| SC-6 | 11.1 | authn-authz + security | `authn-authz` | T-SC-6 | Partial (Phase 1 backend) |
| SC-7 | 11.1 | authn-authz + security | `authn-authz` | T-SC-7 | Not started |
| SC-8 | 11.1 | authn-authz + security | `authn-authz` | T-SC-8 | Partial (Phase 0 skeleton) |
| SC-9 | 11.1 | authn-authz + security | `authn-authz` | T-SC-9 | Not started |
| SM-1 | 9.11 | workflow-builder | `workflow-builder` | T-SM-1 | Not started |
| SM-2 | 9.11 | workflow-builder | `workflow-builder` | T-SM-2 | Not started |
| SM-3 | 9.11 | workflow-builder | `workflow-builder` | T-SM-3 | Not started |
| SM-4 | 9.11 | workflow-builder | `workflow-builder` | T-SM-4 | Not started |
| SM-5 | 9.11 | workflow-builder | `workflow-builder` | T-SM-5 | Not started |
| SM-6 | 9.11 | workflow-builder | `workflow-builder` | T-SM-6 | Not started |
| SM-7 | 9.11 | workflow-builder | `workflow-builder` | T-SM-7 | Not started |
| TS-1 | 12 | guardrails-service | `guardrails-service` | T-TS-1 | Partial (Phase 1 backend) |
| TS-2 | 12 | guardrails-service | `guardrails-service` | T-TS-2 | Partial (Phase 1 backend) |
| TS-3 | 12 | guardrails-service | `guardrails-service` | T-TS-3 | Partial (Phase 1 full-stack) |
| TS-4 | 12 | guardrails-service | `guardrails-service` | T-TS-4 | Partial (Phase 1 backend) |
| TS-5 | 12 | guardrails-service | `guardrails-service` | T-TS-5 | Not started |
| TS-6 | 12 | guardrails-service | `guardrails-service` | T-TS-6 | Partial (Phase 1 backend) |
| TS-7 | 12 | guardrails-service | `guardrails-service` | T-TS-7 | Not started |
| TS-8 | 12 | guardrails-service | `guardrails-service` | T-TS-8 | Not started |
