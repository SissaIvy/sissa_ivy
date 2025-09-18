# RB-001: Quick Fix Identification and Patch Application

**Document Type**: Operational Runbook  
**Status**: Draft  
**Created**: 2025-09-15  
**Last Updated**: 2025-09-15  
**Version**: 1.0  
**Tags**: `troubleshooting`, `patches`, `rollback`, `safety`, `audit-trail`

## Purpose

This runbook provides step-by-step procedures for identifying, categorizing, and safely applying quick fixes while maintaining a complete audit trail. Based on lessons learned from recent quick fix application sessions.

## When to Use This Runbook

- Code hygiene improvements (type hints, docstrings, minor refactoring)
- CLI usability enhancements (help text, flag aliases)
- Safety improvements (bounds checking, error handling)
- Documentation updates and clarifications
- Minor dependency updates

## Pre-Flight Checklist

Before starting any quick fix session:
- [ ] Current branch is up to date with main
- [ ] All existing tests pass
- [ ] Development environment configured
- [ ] Backup plan identified for each intended change
- [ ] Time allocated for full test cycle

## Phase 1: Quick Fix Identification

### Step 1.1: Systematic Code Review
```bash
# Get an overview of the codebase structure
find . -name "*.py" -not -path "./.venv/*" -not -path "./.git/*" | head -20

# Identify potential targets for improvement
grep -r "TODO\|FIXME\|XXX" --include="*.py" --include="*.md" .
```

**Target Categories for Quick Fixes:**

**Low Risk (Green Light)**
- Missing docstrings on public functions
- Type hints for untyped parameters
- CLI help text improvements
- Constant extraction (magic numbers/strings)
- Import organization
- Error message clarity

**Medium Risk (Yellow Light)**
- Bounds checking on numeric inputs
- Exception handling improvements
- Default value safety
- CLI flag additions (non-breaking)
- Logging enhancements

**High Risk (Red Light - Avoid in Quick Fix Sessions)**
- Algorithm changes
- API signature modifications
- Data structure changes
- External dependency changes
- Performance optimizations requiring profiling

### Step 1.2: Create Fix Inventory
Document potential fixes in structured format:

```markdown
## Quick Fix Inventory - Session YYYY-MM-DD

### File: cogsec/collectors/cogsec_probe_linux.py
- [ ] Add docstrings to cpu_percent(), mem_percent(), disk_max_percent()
- [ ] Add type hints to function parameters
- [ ] Extract CPU_SAMPLE_INTERVAL, NET_SAMPLE_INTERVAL constants
- [ ] Add bounds checking for percentage values

### File: normalize_terminology.py
- [ ] Add epilog with usage examples
- [ ] Add short alias for --dry-run flag
- [ ] Improve error messages for missing dependencies

### Risk Assessment:
- Low Risk: 6 items
- Medium Risk: 2 items
- High Risk: 0 items
```

## Phase 2: Safe Patch Application

### Step 2.1: Create Working Branch
```bash
# Use descriptive branch name with date
git checkout -b quickfix/hygiene-improvements-$(date +%Y%m%d)
```

### Step 2.2: Apply Fixes Incrementally

**Pattern**: One logical fix per commit for easy rollback

#### Example: Adding Docstrings and Type Hints
```bash
# Edit file with specific improvements
vim cogsec/collectors/cogsec_probe_linux.py

# Test immediately after each change
python cogsec/collectors/cogsec_probe_linux.py --help
python cogsec/collectors/cogsec_probe_linux.py | python scripts/validate_linux_probe.py -

# Commit with descriptive message
git add cogsec/collectors/cogsec_probe_linux.py
git commit -m "fix: add docstrings and type hints to metrics functions

- Add comprehensive docstrings for cpu_percent, mem_percent, disk_max_percent
- Include parameter and return type hints
- Document error handling behavior
- No functional changes to output format"
```

#### Example: CLI Improvements
```bash
# Edit normalization script
vim normalize_terminology.py

# Test new CLI behavior
python normalize_terminology.py --help
python normalize_terminology.py . -n  # test short alias

# Commit incrementally
git add normalize_terminology.py
git commit -m "feat: add CLI usability improvements to normalize_terminology

- Add epilog with usage examples and exit code documentation
- Add -n short alias for --dry-run flag
- Improve extension handling clarity
- Maintains backward compatibility"
```

### Step 2.3: Continuous Validation

After each commit:
```bash
# Run existing tests
pytest -q

# Validate probe functionality
python cogsec/collectors/cogsec_probe_linux.py --pretty | python scripts/validate_linux_probe.py -

# Check for regressions
python cogsec/collectors/cogsec_probe_linux.py > test_output.json
diff baseline_output.json test_output.json || echo "Expected differences in formatting only"
```

## Phase 3: Quality Assurance

### Step 3.1: Pre-Integration Testing
```bash
# Full test suite
pytest -v

# Validate all CLI combinations
python cogsec/collectors/cogsec_probe_linux.py --pretty --json-path /tmp/test1.json
python cogsec/collectors/cogsec_probe_linux.py --strict --json-path /tmp/test2.json
python scripts/validate_linux_probe.py /tmp/test1.json
python scripts/validate_linux_probe.py /tmp/test2.json

# Test normalization script
python normalize_terminology.py . --check -n  # dry run with new alias
```

### Step 3.2: Documentation Updates
```bash
# Update any affected README sections
vim README.md

# Commit documentation changes
git add README.md
git commit -m "docs: update usage examples for CLI improvements

- Document new -n alias for --dry-run
- Add pretty output examples
- Update Linux probe schema validation section"
```

## Phase 4: Integration and Audit Trail

### Step 4.1: Pre-Merge Review
Create detailed summary of all changes:

```markdown
## Quick Fix Session Summary - 2025-09-15

### Changes Applied:
1. **cogsec_probe_linux.py hygiene improvements**
   - Added docstrings and type hints
   - Extracted constants for intervals
   - Enhanced error handling safety
   - No functional output changes

2. **normalize_terminology.py CLI enhancements**
   - Added -n alias for --dry-run
   - Added epilog with examples
   - Improved help text clarity
   - Maintains full backward compatibility

### Testing Results:
- All existing tests pass: ✅
- Schema validation successful: ✅
- No output format changes: ✅
- CLI backward compatibility: ✅

### Risk Assessment:
- Breaking change risk: None
- Performance impact: None measured
- Rollback complexity: Low (individual commits)

### Rollback Plan:
Each change is in separate commit for selective rollback:
- Probe hygiene: git revert <commit-sha-1>
- CLI enhancements: git revert <commit-sha-2>
- Documentation: git revert <commit-sha-3>
```

### Step 4.2: Final Integration
```bash
# Squash related commits if desired
git rebase -i HEAD~3  # optional for cleaner history

# Push and create PR
git push origin quickfix/hygiene-improvements-$(date +%Y%m%d)

# Create PR with comprehensive description
gh pr create --title "Quick fix: Code hygiene and CLI usability improvements" \
  --body "$(cat quickfix_summary.md)"
```

## Emergency Rollback Procedures

### Individual Fix Rollback
```bash
# Identify problematic commit
git log --oneline -n 10

# Revert specific commit
git revert <commit-sha> --no-edit
git push origin <branch-name>
```

### Complete Session Rollback
```bash
# Reset to pre-session state
git reset --hard origin/main
git push --force-with-lease origin <branch-name>

# Or create clean revert branch
git checkout main
git checkout -b revert/quickfix-session-$(date +%Y%m%d)
git revert <first-commit-sha>..<last-commit-sha>
```

### Emergency Hotfix Process
If quick fix caused production issue:

1. **Immediate Response**
   ```bash
   # Create hotfix branch from main
   git checkout main
   git checkout -b hotfix/revert-quickfix-issue
   
   # Revert problematic changes
   git revert <problematic-commit-sha>
   git push origin hotfix/revert-quickfix-issue
   ```

2. **Escalation**
   - Notify Technical Lead immediately
   - Document issue in incident log
   - Schedule post-mortem review

## Quality Gates and Checkpoints

### Mandatory Checkpoints
- [ ] All tests pass after each commit
- [ ] No functional changes to core output
- [ ] Schema validation passes
- [ ] Documentation updated for user-facing changes
- [ ] Rollback plan tested (at least mentally)

### Optional Quality Enhancements
- [ ] Performance benchmarking for timing-sensitive changes
- [ ] Static analysis tool runs (mypy, pylint)
- [ ] Code coverage maintenance or improvement

## Lessons Learned Integration

### Common Patterns That Work
1. **Incremental commits**: Easier rollback and review
2. **Test-driven fixes**: Validate continuously rather than at end
3. **Documentation-first**: Update help text before implementing new features
4. **Conservative scope**: Focus on hygiene over functionality

### Anti-Patterns to Avoid
1. **Batch commits**: Multiple unrelated changes in single commit
2. **Scope creep**: Adding functionality during hygiene session
3. **Skipping tests**: Assuming "small change" won't break anything
4. **Poor commit messages**: Generic "fix things" messages

## Metrics and Success Criteria

### Session Success Metrics
- Time to complete session: Target < 2 hours
- Rollback events: Target 0 per session
- Test regression incidents: Target 0
- Documentation coverage: 100% of user-facing changes

### Quality Metrics
- Code maintainability improvement: Measured by review feedback
- CLI usability improvement: Measured by help text clarity
- Error handling robustness: Measured by edge case testing

## Related Documents

- **KB-001**: Schema Validation Implementation Patterns
- **SOP-001**: Probe Enhancement Process
- **KB-002**: War Room UI Development Patterns (planned)

---

**Document Owner**: Development Team  
**Emergency Contact**: Technical Lead  
**Next Review Date**: 2025-12-15  
**Usage Frequency**: Weekly quick fix sessions