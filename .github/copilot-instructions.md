# sissa_ivy - Native Endpoint Probes

Native endpoint probes for Windows and Linux that collect basic health and security posture without relying on a heavyweight agent. The probes emit compact JSON records and, for Windows, optionally append CSV lines that match the cogsec_workflow.py health schema.

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Repository Structure

The repository contains three main components:
- **Linux Probe**: `cogsec/collectors/cogsec_probe_linux.py` - Python script for Linux endpoint monitoring
- **Windows Probe**: `cogsec/collectors/Get-CogSecEndpointState.ps1` - PowerShell script for Windows endpoint monitoring  
- **Terminology Normalizer**: `normalize_terminology.py` - Python utility for normalizing terminology across files

## Working Effectively

### Dependencies and Environment Setup
- **Python**: Requires Python 3.8+ (tested with Python 3.12). The system must have standard library modules.
- **PowerShell**: For Windows probe syntax validation, PowerShell Core (`pwsh`) is available but Windows-specific cmdlets will not work on Linux.
- **No build system**: This repository contains scripts that run directly without compilation.

### Validation and Testing Commands

#### Linux Probe Testing
```bash
# Test the Linux probe (runs in ~5 seconds)
python3 cogsec/collectors/cogsec_probe_linux.py
```
**Expected output**: Single line JSON with system metrics including host, timestamp, OS, CPU/memory/disk usage, firewall status, and listening ports.

#### Windows Probe Syntax Validation
```bash
# Validate PowerShell script syntax (runs in ~2 seconds)
pwsh -NoProfile -Command "try { \$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content 'cogsec/collectors/Get-CogSecEndpointState.ps1' -Raw), [ref]\$null); Write-Host 'PowerShell script syntax is valid' } catch { Write-Host 'PowerShell script has syntax errors:' \$_ }"
```
**Expected output**: "PowerShell script syntax is valid"

#### Terminology Normalizer Testing
```bash
# Test terminology normalizer help - WILL FAIL due to missing dependency
python3 normalize_terminology.py --help
```
**Expected output**: `Failed to import 'terminology_normalizer.normalize': No module named 'terminology_normalizer'`

**CRITICAL DEPENDENCY ISSUE**: The `normalize_terminology.py` script requires a `terminology_normalizer.py` module with a `normalize()` function. This dependency is missing from the repository. The script will fail with import error until this module is provided.

### Manual Validation Requirements

**ALWAYS test actual functionality after making changes:**

1. **Linux Probe Validation**:
   - Run `python3 cogsec/collectors/cogsec_probe_linux.py`
   - Verify JSON output contains all expected fields: host, timestamp, os, cpu, mem, disk, net_in, net_out, firewall, controls, listening_ports
   - Confirm numeric values are reasonable (CPU 0-100%, memory 0-100%, disk 0-100%)

2. **Windows Probe Validation**:
   - Run syntax validation command above
   - Verify no PowerShell syntax errors are reported
   - **Note**: Full Windows probe functionality cannot be tested on Linux systems

3. **Terminology Normalizer Validation**:
   - **Note**: This script currently has missing dependencies and will fail
   - Run `python3 normalize_terminology.py --help` to confirm import error
   - Expected error: `Failed to import 'terminology_normalizer.normalize': No module named 'terminology_normalizer'`

## Common Tasks and Troubleshooting

### File Locations
```
Repository root structure:
├── .github/                    # GitHub configuration
├── LICENSE                     # Repository license
├── README.md                   # Main documentation
├── cogsec/                     # Main probe directory
│   └── collectors/             # Probe scripts
│       ├── Get-CogSecEndpointState.ps1  # Windows probe
│       └── cogsec_probe_linux.py        # Linux probe
├── normalize_terminology.py    # Terminology normalizer (missing dependencies)
└── terminology_normalizer.py   # MISSING: Required module for normalizer
```

### Known Issues and Workarounds

1. **Missing terminology_normalizer module**: The `normalize_terminology.py` script requires a `terminology_normalizer.py` module with a `normalize()` function. This dependency is currently missing from the repository, causing import errors when trying to run the script.

2. **PowerShell limitations on Linux**: Windows-specific cmdlets (WMI/CIM, Defender) will not work in PowerShell Core on Linux. Only syntax validation is possible.

3. **No build system**: This repository contains executable scripts only. No compilation, building, or dependency installation is required.

### Timeout Specifications

Most validation commands complete quickly:
- Linux probe execution: ~5 seconds
- PowerShell syntax validation: ~2 seconds  
- Terminology normalizer: Immediate failure due to missing dependency
- **Use default timeouts (120 seconds) - no extended timeouts needed**

### Validation Scenarios

**After making any changes, ALWAYS run this complete validation sequence:**

```bash
# Complete validation (total time: ~10 seconds)
echo "=== Testing Linux Probe ==="
python3 cogsec/collectors/cogsec_probe_linux.py

echo -e "\n=== Validating Windows Probe Syntax ==="
pwsh -NoProfile -Command "try { \$null = [System.Management.Automation.PSParser]::Tokenize((Get-Content 'cogsec/collectors/Get-CogSecEndpointState.ps1' -Raw), [ref]\$null); Write-Host 'PowerShell script syntax is valid' } catch { Write-Host 'PowerShell script has syntax errors:' \$_ }"

echo -e "\n=== Testing Terminology Normalizer (will show dependency error) ==="
python3 normalize_terminology.py --help

echo -e "\n=== All validations complete ==="
```

### Quick Reference Commands

```bash
# Repository exploration
ls -la                                    # List all files
find . -name "*.py" -o -name "*.ps1"     # Find all scripts

# Python environment check  
python3 --version                        # Check Python version
python3 -c "import sys; print(sys.path)" # Check Python path

# PowerShell environment check
pwsh -Command "Write-Host 'PowerShell is working'" # Test PowerShell

# File permission verification
ls -l cogsec/collectors/                  # Check script permissions
```

## CI/Build Information

- **No CI/CD**: This repository does not have GitHub Actions or other CI systems configured.
- **No tests**: No automated test suite exists.
- **No linting**: No code quality tools are configured.
- **No builds**: Scripts run directly without compilation.

## Development Guidelines

- **Always validate scripts before committing**: Run the complete validation sequence above.
- **Preserve script functionality**: Ensure JSON output format remains consistent for downstream consumers.
- **Cross-platform considerations**: Remember that Windows probe uses Windows-specific APIs that won't work on Linux.
- **Security considerations**: These are security monitoring tools - ensure any changes don't compromise security posture collection.

## Architecture Notes

This is a **lightweight monitoring solution** designed for:
- Minimal system impact (no persistent agents)
- Compact data output (JSON format)
- Cross-platform endpoint monitoring
- Integration with log forwarding systems (Cribl Edge mentioned in README)

The probes are designed to be scheduled (Windows Task Scheduler, Linux systemd timers) and emit structured data for downstream processing.