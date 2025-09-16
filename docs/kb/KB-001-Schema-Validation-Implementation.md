# KB-001: Schema Validation Implementation Patterns

**Document Type**: Knowledge Base Article  
**Status**: Draft  
**Created**: 2025-09-15  
**Last Updated**: 2025-09-15  
**Tags**: `schema`, `validation`, `type-safety`, `backward-compatibility`, `cli-refactoring`

## Executive Summary

Implementation of JSON Schema validation for Linux probe output revealed key patterns for maintaining backward compatibility while adding structural validation. This article captures lessons learned, type safety considerations, and CLI refactoring approaches that can be applied to future probe enhancements.

## Context

During the enhancement of the Linux probe (`cogsec/collectors/cogsec_probe_linux.py`), we needed to:
1. Add formal JSON Schema validation without breaking existing consumers
2. Refactor CLI interface while preserving current output format
3. Implement type-safe validation with proper error handling
4. Integrate validation into development workflow

## Technical Lessons Learned

### 1. Schema Design for Backward Compatibility

**Challenge**: Existing probe output used specific field names (`net_in`, `net_out`, nested `firewall` object) that could conflict with future standardization efforts.

**Solution**: Preserved existing field structure in schema rather than imposing new naming conventions.

```json
{
  "required": [
    "host", "timestamp", "os", "cpu", "mem", "disk", 
    "net_in", "net_out", "firewall", "controls", "listening_ports"
  ],
  "properties": {
    "net_in": { "type": "integer", "minimum": 0 },
    "net_out": { "type": "integer", "minimum": 0 },
    "firewall": {
      "type": "object",
      "required": ["manager", "enabled"],
      "properties": {
        "manager": { "type": ["string", "null"] },
        "enabled": { "type": ["boolean", "null"] }
      }
    }
  }
}
```

**Key Insight**: Additive schema evolution is safer than field renaming. Future versions can introduce alias fields while maintaining original structure.

### 2. CLI Refactoring Without Breaking Changes

**Challenge**: Need to add CLI flags (`--json-path`, `--pretty`, `--strict`) while preserving default stdout behavior.

**Pattern Applied**: Extract core logic into `collect_record()` function, maintain existing `main()` behavior as default.

```python
def collect_record() -> Dict[str, object]:
    """Build and return the probe record dictionary."""
    # Core logic extracted for reusability
    
def main() -> int:
    """CLI entrypoint: gather metrics and emit JSON record."""
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    
    record = collect_record()  # Reusable core
    # Handle CLI flags while preserving defaults
```

**Key Insight**: Separation of data collection from output formatting enables flexible CLI without breaking existing integrations.

### 3. Type Safety in Dynamic Validation Context

**Challenge**: Type checker complained about `record.get('cpu')` returning `object` when casting to `float` for strict validation.

**Anti-Pattern**: Using `# type: ignore` to suppress warnings.

**Better Pattern**: Defensive helper functions that handle type uncertainty:

```python
def safe_float(val: object) -> float:
    try:
        return float(val)  # type: ignore[arg-type]
    except Exception:
        return 0.0

# Usage in strict validation
cpu = safe_float(record.get('cpu'))
```

**Key Insight**: Explicit uncertainty handling is better than blanket type ignoring, especially at system boundaries.

### 4. Validation Script Design Patterns

**Pattern**: Stdin support with clear exit codes for CI integration:

```python
def main(argv: list[str]) -> int:
    record = load_record(argv[1])  # Support '-' for stdin
    schema = load_schema()
    try:
        jsonschema.validate(instance=record, schema=schema)
    except jsonschema.ValidationError as ve:
        print(f"[validate] FAILED: {ve.message}", file=sys.stderr)
        return 1  # Schema violation
    print("[validate] OK")
    return 0  # Success

# Exit codes: 0=valid, 1=schema failure, 2=usage/IO error
```

**Key Insight**: Consistent exit code semantics enable reliable CI integration and scripting.

## Architectural Decisions

### Decision 1: Schema Location and Naming
- **Chosen**: `schema/linux_probe.schema.json`  
- **Alternative**: Embedded schema in Python code  
- **Rationale**: External files enable tooling integration and version control

### Decision 2: Validation Library Choice
- **Chosen**: `jsonschema` library with pinned version  
- **Alternative**: Custom validation logic  
- **Rationale**: Standard library with good error messages and JSON Schema draft compliance

### Decision 3: CLI Flag Naming
- **Chosen**: `--json-path`, `--pretty`, `--strict`  
- **Alternative**: Short flags only (`-o`, `-p`, `-s`)  
- **Rationale**: Descriptive long flags improve script readability and self-documentation

## Implementation Anti-Patterns Avoided

1. **Breaking Change Trap**: Renaming existing fields in schema to match "ideal" naming
2. **Type Erasure**: Over-using `Any` or `object` types without validation helpers  
3. **Monolithic Main**: Combining data collection, formatting, and output in single function
4. **Silent Failures**: Validation errors without clear exit codes or error messages
5. **Tight Coupling**: Validator script dependent on specific file paths or probe internals

## Rollback Procedures

### Quick Rollback (Emergency)
```bash
# Remove new files
rm -f schema/linux_probe.schema.json
rm -f scripts/validate_linux_probe.py

# Revert probe changes
git checkout HEAD~1 -- cogsec/collectors/cogsec_probe_linux.py

# Restore requirements
git checkout HEAD~1 -- requirements.txt
```

### Validation Rollback (CI Failure)
```bash
# Disable validation step in CI temporarily
git revert <validation-commit-hash> --no-edit
```

### Schema Evolution Rollback
```bash
# Keep validator but use previous schema version
cp schema/linux_probe.schema.json.backup schema/linux_probe.schema.json
```

## Future Evolution Patterns

### Adding Optional Fields
```json
{
  "properties": {
    "schema_version": { "type": "string" },  // Add optional metadata
    "collection_duration_ms": { "type": "number", "minimum": 0 }  // Add timing
  }
}
```

### Field Deprecation Process
1. Add new canonical field alongside old field
2. Update schema to accept both (with deprecation note)
3. Update documentation with migration timeline
4. Remove old field after deprecation window

### Multi-Platform Schema Unification
```json
{
  "oneOf": [
    { "$ref": "#/$defs/linux_probe" },
    { "$ref": "#/$defs/windows_probe" }
  ]
}
```

## Metrics and Success Criteria

### Implementation Success Metrics
- ✅ Zero breaking changes to existing probe output format
- ✅ All existing tests continue to pass
- ✅ New CLI flags work without affecting default behavior
- ✅ Validator catches schema violations with clear error messages

### Operational Success Metrics (Future)
- Validation integrated into CI pipeline
- Schema evolution without breaking downstream consumers
- Reduced debugging time for malformed probe output
- Improved documentation through executable schema

## Related Documents

- **SOP-001**: Probe Enhancement Process
- **RB-001**: Quick Fix Identification and Patch Application
- Project README: Linux Probe Schema & Validation section

## Review and Maintenance

**Next Review Date**: 2025-12-15  
**Review Criteria**: Accuracy of patterns, effectiveness in practice, new lessons learned  
**Update Triggers**: Major schema changes, validation framework updates, type system changes

---

**Document Owner**: Development Team  
**Approver**: Technical Lead  
**Distribution**: All developers working on probe enhancements