# SOP-001: Probe Enhancement Process

**Document Type**: Standard Operating Procedure  
**Status**: Draft  
**Created**: 2025-09-15  
**Last Updated**: 2025-09-15  
**Version**: 1.0  
**Tags**: `probe`, `enhancement`, `workflow`, `validation`, `process`

## Purpose

This SOP defines the standardized workflow for enhancing endpoint probes (Linux and Windows) to ensure consistency, quality, and maintainability while preserving backward compatibility and following SISSA Mastermind guardrails.

## Scope

Applies to all modifications of:
- `cogsec/collectors/cogsec_probe_linux.py`
- `cogsec/collectors/Get-CogSecEndpointState.ps1`
- Associated schemas, validators, and tests

## Roles and Responsibilities

- **Developer**: Implements enhancement following this procedure
- **Technical Lead**: Reviews schema changes and breaking change assessments
- **QA**: Validates test coverage and integration testing
- **DevOps**: Ensures CI/CD pipeline integration

## Prerequisites

- [ ] Python virtual environment configured (`configure_python_environment`)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Existing tests passing (`pytest -q`)
- [ ] Current branch up to date with main

## Procedure

### Phase 1: Analysis and Planning (A02 Alignment)

**Duration**: 30-60 minutes  
**Inputs**: Enhancement request, current probe output  
**Outputs**: Enhancement plan, breaking change assessment

#### Step 1.1: Requirement Analysis
```bash
# Capture current probe output for baseline
python cogsec/collectors/cogsec_probe_linux.py --pretty > baseline_output.json

# Document requirements in enhancement plan
```

1. **Document Enhancement Scope**
   - What new data will be collected?
   - What existing data structures might change?
   - What are the performance implications?

2. **Assess Breaking Change Risk**
   - Field additions: ✅ Safe (additive)
   - Field renames: ⚠️ Requires deprecation process
   - Field removals: ❌ Breaking change
   - Type changes: ❌ Breaking change
   - Structure changes: ❌ Breaking change

3. **Plan Backward Compatibility Strategy**
   - For additive changes: Update schema, add optional fields
   - For breaking changes: Implement deprecation timeline (see KB-001)

#### Step 1.2: Create Enhancement Branch
```bash
git checkout -b enhancement/probe-<feature-name>
```

### Phase 2: Schema Design (A04 Data Gather)

**Duration**: 45-90 minutes  
**Inputs**: Baseline output, requirements  
**Outputs**: Updated schema, validation plan

#### Step 2.1: Update JSON Schema
```bash
# Edit appropriate schema file
vim schema/linux_probe.schema.json  # for Linux
# or
vim schema/windows_probe.schema.json  # for Windows (future)
```

**Schema Update Checklist:**
- [ ] Add new fields as optional unless absolutely required
- [ ] Include appropriate type constraints and bounds
- [ ] Add descriptive comments for complex structures
- [ ] Validate schema syntax with JSON Schema validator
- [ ] Document schema changes in commit message

#### Step 2.2: Test Schema Changes
```bash
# Generate fresh probe output
python cogsec/collectors/cogsec_probe_linux.py > test_output.json

# Validate against updated schema
python scripts/validate_linux_probe.py test_output.json
```

### Phase 3: Implementation (A06 Evaluate)

**Duration**: 1-3 hours  
**Inputs**: Updated schema, implementation plan  
**Outputs**: Enhanced probe code, updated CLI

#### Step 3.1: Implement Data Collection
```python
# In cogsec/collectors/cogsec_probe_linux.py

def new_metric_function() -> ReturnType:
    """Collect new metric data with error handling."""
    try:
        # Implementation here
        return result
    except Exception:
        return safe_default_value

def collect_record() -> Dict[str, object]:
    """Update to include new metrics."""
    # ... existing code ...
    rec['new_field'] = new_metric_function()
    return rec
```

**Implementation Checklist:**
- [ ] Follow existing error handling patterns (return safe defaults)
- [ ] Maintain performance requirements (< 2 seconds execution)
- [ ] Add appropriate type hints
- [ ] Include docstrings for new functions
- [ ] Preserve existing field order and structure

#### Step 3.2: Update CLI Interface (if needed)
```python
# Add new CLI flags only if enhancement requires user control
parser.add_argument('--new-flag', help='Description of new functionality')
```

### Phase 4: Testing and Validation (A07 Risk)

**Duration**: 1-2 hours  
**Inputs**: Enhanced probe, updated schema  
**Outputs**: Test coverage, validation results

#### Step 4.1: Unit Testing
```bash
# Run existing tests to ensure no regressions
pytest -q tests/test_cogsec_probe_linux.py

# Add new tests for enhanced functionality
# Edit tests/test_linux_probe_schema.py
```

**Test Cases Required:**
- [ ] Positive validation: new output validates against schema
- [ ] Negative validation: invalid new data fails validation
- [ ] Backward compatibility: existing consumers still work
- [ ] Error handling: failures degrade gracefully
- [ ] Performance: execution time within limits

#### Step 4.2: Integration Testing
```bash
# Test end-to-end workflow
python cogsec/collectors/cogsec_probe_linux.py | python scripts/validate_linux_probe.py -

# Test with all CLI flags
python cogsec/collectors/cogsec_probe_linux.py --pretty --strict --json-path enhanced_output.json
python scripts/validate_linux_probe.py enhanced_output.json
```

#### Step 4.3: Documentation Updates
- [ ] Update README.md with new capabilities
- [ ] Add examples of new output format
- [ ] Document any new CLI flags
- [ ] Update relevant KB articles

### Phase 5: Review and Integration (A09 Decision Gate)

**Duration**: 30-60 minutes  
**Inputs**: Complete enhancement with tests  
**Outputs**: Approved changes ready for merge

#### Step 5.1: Self-Review Checklist
- [ ] All tests pass (`pytest -q`)
- [ ] No breaking changes introduced
- [ ] Schema validates successfully
- [ ] Documentation updated
- [ ] Performance requirements met
- [ ] Error handling follows patterns
- [ ] Rollback plan documented

#### Step 5.2: Prepare Pull Request
```bash
# Commit changes with descriptive messages
git add .
git commit -m "feat(probe): add <enhancement-description>

- Add new metric collection for <purpose>
- Update schema with optional fields
- Maintain backward compatibility
- Add validation tests

Closes #<issue-number>"

# Push and create PR
git push origin enhancement/probe-<feature-name>
```

**PR Description Template:**
```markdown
## Enhancement Summary
Brief description of what was added/changed.

## Breaking Change Assessment
- [ ] No breaking changes
- [ ] Breaking changes with migration plan
- [ ] Schema version bump required

## Testing Performed
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual validation successful
- [ ] Performance within limits

## Rollback Plan
Steps to revert if issues discovered:
1. Revert commit hash: `<commit-sha>`
2. Schema rollback: `<procedure>`
3. Dependency rollback: `<if-applicable>`
```

### Phase 6: Post-Integration (A12 Review)

**Duration**: 15-30 minutes  
**Inputs**: Merged enhancement  
**Outputs**: Updated documentation, lessons learned

#### Step 6.1: Verify Integration
```bash
# After merge, verify on main branch
git checkout main
git pull origin main
pytest -q
python cogsec/collectors/cogsec_probe_linux.py | python scripts/validate_linux_probe.py -
```

#### Step 6.2: Update Knowledge Base
- [ ] Add any new lessons learned to relevant KB articles
- [ ] Update this SOP if process gaps discovered
- [ ] Document any unexpected challenges or solutions

## Emergency Procedures

### Rollback Process
If critical issues discovered post-deployment:

```bash
# Immediate rollback
git revert <enhancement-commit-sha> --no-edit
git push origin main

# For schema issues specifically
cp schema/linux_probe.schema.json.backup schema/linux_probe.schema.json
git commit -am "emergency: rollback schema changes"
git push origin main
```

### Escalation Triggers
Contact Technical Lead immediately if:
- Breaking changes discovered in production
- Performance degradation > 50% increase in execution time
- Validation failures in CI pipeline
- Schema corruption or parsing errors

## Quality Gates

### Mandatory Checks
All steps must pass before proceeding to next phase:
- [ ] No regressions in existing functionality
- [ ] Schema validation passes for new output
- [ ] Performance within 2-second limit
- [ ] Test coverage maintained or improved
- [ ] Documentation updated

### Optional Enhancements
Consider for future iterations:
- [ ] Add schema versioning if not present
- [ ] Implement metric history/trending
- [ ] Add structured logging
- [ ] Consider multi-platform schema unification

## Metrics and KPIs

### Process Metrics
- Time to implement enhancement: Target < 4 hours
- Test coverage percentage: Maintain > 80%
- Rollback frequency: Target < 5% of enhancements

### Quality Metrics
- Validation success rate: Target > 99%
- Performance regression incidents: Target 0
- Breaking change incidents: Target 0

## Related Documents

- **KB-001**: Schema Validation Implementation Patterns
- **RB-001**: Quick Fix Identification and Patch Application
- **Project README**: Linux Probe Schema & Validation section

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-09-15 | Initial SOP creation | Development Team |

---

**Document Owner**: Technical Lead  
**Next Review Date**: 2026-03-15  
**Approval Required**: Technical Lead sign-off for all probe enhancements