# Endpoint Telemetry & Orchestration Architecture (Version 1.0)

> Frozen reference snapshot derived from `docs/architecture.md` at schema_version 1.1.1 timeframe. Future evolutions SHOULD add a new versioned file (e.g. `_v_1_1.md`) while keeping this immutable for audit and historical comparison.

## Purpose
Provide a pragmatic evolution path from local probe JSON output to a Salesforce-integrated orchestration and compliance surface without over-building early.

## Phase Overview
| Phase | Goal | Key Components | Exit Criteria |
|-------|------|----------------|---------------|
| 0 | Contract & Feasibility | JSON schema, prototype ingestion | Stable 1.x schema; validator adopted |
| 1 | Inventory & Health MVP | Probes → Ingestion → Summary DB → SF External Objects | Host list + health metrics visible in SF |
| 2 | Compliance & Patch Delta | Rules engine, materialized summaries, events | Compliance % & patch gap dashboards |
| 3 | Remote Actions | Command queue, signed tasks, evidence store | Controlled remediation with audit trail |
| 4 | Advanced Query | Columnar/time-series index, filter UI | Ad-hoc queries < 5s for >10k endpoints |
| 5 | Mesh / Acceleration (Optional) | Relay/peer overlay, edge caches | Sub-second partial-fleet answers |

## Data Model (Logical)
```
EndpointState(host, last_seen, os, cpu, mem, disk, firewall_enabled, rdp_enabled, risk_score, json_blob)
EndpointMetric(host, ts, cpu, mem, disk, net_in_bps, net_out_bps)
ComplianceFinding(host, rule_id, status, severity, evidence_ref, last_observed)
ActionRequest(id, created_ts, creator, host_scope_expr, command_type, params_json, status, updated_ts)
ActionResult(action_id, host, ts, status, output_ref, duration_ms)
EventLog(id, ts, category, subject, payload_json, integrity_hash)
```

## JSON Schema Strategy
- Line 1.x = additive & deprecation only; no required field removals.
- `schema_version` gate used by ingestion to choose parser branch (future).
- Deprecations: introduce canonical field + alias, mark removal no earlier than next minor after introduction.

## Ingestion & Validation
- Current prototype: `platform/ingestion_service.py` + SQLite.
- Production path: API gateway → queue → validation worker → durable DB.
- Reject invalid payloads (no partial acceptance) to prevent silent drift.

## Salesforce Integration Patterns
| Use Case | Pattern |
|----------|---------|
| Current state dashboards | External Objects (OData/GraphQL gateway) |
| Change notifications | Platform Events (summary deltas) |
| Workflows / Approvals | Flow + Apex triggers referencing External Objects |
| Heavy result grids | Canvas embedding external React UI |
| Remediation command issue | LWC form → Apex callout → Command service |

## Remote Action Security
1. All commands stored with immutable ID & hash of payload.
2. Endpoints poll, authenticate (mTLS or token + device key), receive tasks.
3. Endpoint returns signed result manifest + (optional) artifact pointer.
4. Audit log append-only (hash chained) for non-repudiation.

## Scaling Considerations
| Concern | Early | Scale Path |
|---------|-------|-----------|
| Storage | SQLite | PostgreSQL/Timescale or ClickHouse |
| Query latency | Direct DB | Materialized views + caching layer |
| High cardinality metrics | Append-only table | Roll-up (hour/day) + cold archive (object store) |
| Multi-tenant isolation | DB schema per tenant | Row-level security + per-tenant encryption keys |

## KPIs
- Probe success rate ≥ 98%
- Ingestion validation failure < 0.5% (excluding test data)
- Summary freshness SLA: ≤ 5 min (Phase 2+)
- Remote action median completion: < 120s (Phase 3)

## Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| Schema sprawl | Version discipline + automated validation gate |
| Overloading Salesforce limits | Pre-aggregate externally; limit row counts per view |
| Command spoofing | Strong device identity + signed payloads |
| Data exfiltration via actions | Whitelisted command catalog + approval workflow |
| Silent collector failures | Heartbeat detection (last_seen gap alert) |

## Future Enhancements (Backlog)
- gRPC streaming ingestion (long-lived) for lower overhead.
- Host-level differential compression for large JSON payloads.
- Integrity transparency log (Merkle root published per batch).
- Risk scoring plugin framework (weighted multi-factor model).

---
Change Management:
- This file is immutable once merged; amendments go into a new versioned file.
- Referenced schema: `schema/endpoint_state.schema.json` (1.1.1 era).

Provenance:
- Origin branch: codex/add-section-for-autolearncorrectllm-spec
- Generated date (UTC): 2025-09-15
