# Ordnance Agent Artifact Tagging — Patch v1.0

**Version:** 1.0  
**Date:** 2025-09-16  
**Classification:** OPERATIONAL  
**Teams:** Ordnance (S-4), BlackOps (S-3), PsyOps (S-5)

---

## Executive Summary

This document establishes the standardized artifact tagging methodology for the Ordnance Agent ecosystem, enabling consistent tracking, correlation, and automated processing of vulnerability intelligence artifacts across BlackOps and PsyOps workflows.

---

## Purpose & Scope

### Purpose
- Define artifact tagging schema for vulnerability reports, patch intelligence, and endpoint telemetry
- Establish automated tagging workflows for consistent metadata application
- Enable cross-team artifact correlation and workflow orchestration
- Support compliance and audit requirements for vulnerability management

### Scope
- **In Scope:** JSON artifacts, CSV reports, endpoint telemetry, patch intelligence, vulnerability findings
- **Out of Scope:** Source code artifacts, build outputs, deployment manifests (covered by separate processes)

---

## Artifact Taxonomy

### Core Artifact Types

#### 1. Vulnerability Intelligence (`vuln`)
- **Purpose:** CVE findings, CVSS scores, KEV flags, exposure analysis
- **Sources:** Ordnance scans, external feeds, manual assessments
- **Retention:** 2 years (active), 7 years (archived)

#### 2. Patch Intelligence (`patch`)
- **Purpose:** Missing KB tracking, compliance percentages, remediation status
- **Sources:** Endpoint probes, Windows Update APIs, manual verification
- **Retention:** 1 year (active), 3 years (archived)

#### 3. Endpoint Telemetry (`endpoint`)
- **Purpose:** Health metrics, posture data, configuration state
- **Sources:** CogSec probes (Windows/Linux), agent telemetry
- **Retention:** 90 days (active), 1 year (archived)

#### 4. Operational Reports (`ops`)
- **Purpose:** JAO summaries, action results, workflow outcomes
- **Sources:** BlackOps/PsyOps execution, automated workflows
- **Retention:** 3 years (compliance)

---

## Tagging Schema

### Standard Tag Structure
```
{artifact_type}:{subtype}:{classification}:{team}:{timestamp}:{sequence}
```

### Tag Components

#### Artifact Type
- `vuln` - Vulnerability intelligence
- `patch` - Patch management data
- `endpoint` - Endpoint telemetry
- `ops` - Operational reports

#### Subtype
- **Vulnerability:** `finding`, `assessment`, `correlation`, `feed`
- **Patch:** `missing`, `compliance`, `status`, `manifest`
- **Endpoint:** `health`, `posture`, `config`, `probe`
- **Operational:** `jao`, `result`, `summary`, `evidence`

#### Classification
- `open` - Unclassified operational data
- `restricted` - Internal team use only
- `confidential` - Sensitive operational intelligence

#### Team
- `s3` - BlackOps (S-3 Ops Intel)
- `s4` - Ordnance (S-4 Patch Recon)
- `s5` - PsyOps (S-5 Change Execution)
- `cross` - Cross-team collaboration

#### Timestamp
- Format: `YYYYMMDD-HHMM` (UTC)
- Example: `20250916-1430`

#### Sequence
- 3-digit incrementing counter per day
- Example: `001`, `002`, `127`

### Example Tags
```
vuln:finding:restricted:s4:20250916-1430:001
patch:missing:open:s4:20250916-1435:002
endpoint:health:open:s3:20250916-1440:003
ops:jao:restricted:cross:20250916-1445:004
```

---

## Artifact Metadata Schema

### Required Fields (All Artifacts)
```json
{
  "artifact_id": "string",
  "tag": "string",
  "generated_at": "ISO8601",
  "expires_at": "ISO8601",
  "source_system": "string",
  "source_version": "string",
  "schema_version": "1.0",
  "checksum": "sha256",
  "file_size_bytes": "integer"
}
```

### Vulnerability Specific Fields
```json
{
  "cve_id": "string",
  "cvss_score": "float",
  "severity": "enum[CRITICAL,HIGH,MEDIUM,LOW]",
  "kev_listed": "boolean",
  "affected_assets": ["array"],
  "remediation_available": "boolean",
  "evidence_refs": ["array"]
}
```

### Patch Specific Fields
```json
{
  "kb_id": "string",
  "patch_tuesday": "YYYY-MM",
  "superseded_by": "string|null",
  "reboot_required": "boolean",
  "missing_count": "integer",
  "total_assets": "integer",
  "compliance_pct": "float"
}
```

### Endpoint Specific Fields
```json
{
  "host_id": "string",
  "os_family": "enum[windows,linux]",
  "last_seen": "ISO8601",
  "probe_version": "string",
  "health_status": "enum[healthy,degraded,critical]",
  "config_drift": "boolean"
}
```

---

## Automation Workflows

### Auto-Tagging Pipeline

#### Trigger Events
- New artifact detected in staging area
- Scheduled bulk processing (hourly)
- Manual tag refresh request

#### Processing Steps
1. **Artifact Detection**
   - Monitor `reports/` directories for new files
   - Validate file format and basic structure
   - Queue for tagging pipeline

2. **Content Analysis**
   - Extract artifact type from file structure
   - Parse metadata fields
   - Determine classification level

3. **Tag Generation**
   - Generate timestamp and sequence
   - Apply team assignment rules
   - Create full tag string

4. **Metadata Injection**
   - Add tagging metadata to artifact
   - Calculate checksums
   - Set expiration dates

5. **Artifact Promotion**
   - Move to appropriate storage tier
   - Update artifact registry
   - Trigger downstream workflows

### Integration Points

#### BlackOps (S-3) Integration
- **Input:** Tagged vulnerability and endpoint artifacts
- **Output:** Assessment reports, evidence packages
- **Workflow:** Automated threat correlation, exposure analysis

#### PsyOps (S-5) Integration
- **Input:** Tagged patch and operational artifacts
- **Output:** Execution manifests, result summaries
- **Workflow:** Remediation orchestration, change tracking

#### Ordnance (S-4) Integration
- **Input:** Raw scan data, probe telemetry
- **Output:** Tagged intelligence artifacts
- **Workflow:** Continuous intelligence generation, correlation analysis

---

## CLI Interface

### Ordnance Agent Commands

#### Tag Artifact
```bash
python agents/ordnance_agent.py tag \
  --input reports/patch/latest.json \
  --type patch:missing \
  --classification open \
  --team s4
```

#### Bulk Tag Operation
```bash
python agents/ordnance_agent.py tag-bulk \
  --input-dir reports/probe/ \
  --pattern "*.json" \
  --type endpoint:health \
  --classification open \
  --team s3
```

#### Query Tagged Artifacts
```bash
python agents/ordnance_agent.py query \
  --tag-pattern "vuln:finding:*:s4:*" \
  --since "2025-09-15" \
  --format table
```

#### Validate Tags
```bash
python agents/ordnance_agent.py validate \
  --input reports/tagged/ \
  --check-expiry \
  --verify-checksums
```

---

## Storage & Retention

### Storage Tiers

#### Hot Storage (0-30 days)
- **Location:** `reports/active/`
- **Access:** Direct filesystem, API queries
- **Backup:** Daily incremental

#### Warm Storage (30-365 days)
- **Location:** `reports/archive/`
- **Access:** API queries, batch retrieval
- **Backup:** Weekly full

#### Cold Storage (1+ years)
- **Location:** External object storage
- **Access:** Batch retrieval only
- **Backup:** Monthly verification

### Retention Policies

#### Automatic Cleanup
- Hot → Warm: 30 days after generation
- Warm → Cold: 365 days after generation
- Cold → Deletion: Per artifact type retention period

#### Manual Retention Holds
- Legal hold: Prevent deletion indefinitely
- Operational hold: Extend retention for ongoing incidents
- Compliance hold: Audit-related preservation

---

## Compliance & Auditing

### Audit Trail Requirements
- All tagging operations logged with user attribution
- Metadata changes tracked with before/after states
- Artifact access logged with timestamp and purpose
- Retention policy applications recorded

### Compliance Mappings
- **SOC 2:** Artifact integrity, access controls, retention
- **ISO 27001:** Information classification, handling procedures
- **NIST CSF:** Vulnerability management, incident response artifacts

### Reporting
- Monthly artifact volume and storage utilization
- Quarterly retention policy compliance status
- Annual audit trail integrity verification

---

## Rollback & Recovery

### Tag Rollback Scenarios
1. **Incorrect Classification:** Re-tag with corrected classification level
2. **Wrong Team Assignment:** Update team field and notify affected workflows
3. **Metadata Corruption:** Restore from checksum verification and re-tag
4. **Schema Changes:** Migrate existing tags to new schema version

### Recovery Procedures
1. **Identify Impact:** Determine affected artifacts and downstream systems
2. **Isolate Changes:** Prevent further automated processing during correction
3. **Correct Tags:** Apply fixes using validated correction scripts
4. **Verify Integrity:** Run checksum validation and metadata consistency checks
5. **Resume Operations:** Re-enable automated workflows and notify teams

### Rollback Commands
```bash
# Rollback specific tag
python agents/ordnance_agent.py rollback \
  --artifact-id vuln:finding:restricted:s4:20250916-1430:001 \
  --reason "incorrect classification"

# Bulk rollback by pattern
python agents/ordnance_agent.py rollback-bulk \
  --tag-pattern "*:*:confidential:s3:20250916-*" \
  --new-classification restricted \
  --reason "classification correction"
```

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Implement tagging schema validation
- [ ] Create artifact registry database
- [ ] Build CLI interface for manual operations
- [ ] Establish storage tier structure

### Phase 2: Automation
- [ ] Deploy auto-tagging pipeline
- [ ] Integrate with existing probe workflows
- [ ] Implement retention policy automation
- [ ] Create monitoring and alerting

### Phase 3: Team Integration
- [ ] BlackOps workflow integration
- [ ] PsyOps orchestration hooks
- [ ] Cross-team artifact sharing protocols
- [ ] Training and documentation rollout

### Phase 4: Compliance & Monitoring
- [ ] Audit trail implementation
- [ ] Compliance reporting automation
- [ ] Performance monitoring dashboards
- [ ] Incident response procedures

---

## Contact & Escalation

### Primary Contacts
- **Ordnance (S-4) Lead:** Artifact schema and retention policies
- **BlackOps (S-3) Lead:** Classification and security requirements
- **PsyOps (S-5) Lead:** Workflow integration and automation

### Escalation Path
1. **Technical Issues:** Ordnance team lead
2. **Classification Disputes:** Security leadership
3. **Compliance Questions:** Audit and compliance team
4. **Cross-Team Conflicts:** Operations leadership

---

**Document Owner:** Ordnance (S-4)  
**Next Review:** 2025-12-16  
**Version Control:** Track changes in `.github/` directory