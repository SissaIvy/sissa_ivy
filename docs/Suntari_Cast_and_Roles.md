## Cast & Roles — Allegory → System Map

- Gatewarden Ishara: API Management (policy checks, schema, rate limits)
- Archivist Nyla: Azure Function (relation→insight engine)
- Kestrel (Lookout): Tier1Detector (fast anomaly score)
- Rune (Tactician): Tier2Responder (action plan)
- Kael (Hunter): Tier3Hunter (approval/escalation)
- Iron Wardens: EndpointOverlay (isolate/kill/quarantine/notify)
- River Sentinels: NetworkOverlay (block/rate‑limit/sinkhole/revoke)
- Vault Scribes: DatabaseOverlay (lock/rotate/restrict/maint‑mode)
- Strict Lantern: profile=strict (hard validation, deterministic)
- Exploratory Lantern: profile=explore (tolerant, still logged)

Notes
- No runtime renames required; use allegory labels in docs, dashboards, and runbooks.
- Tag telemetry (customDimensions) with cast names to enable story‑first dashboards.

