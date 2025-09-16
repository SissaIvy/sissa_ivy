# RB-002: Development Environment Setup and Troubleshooting

**Document Type**: Operational Runbook  
**Status**: Draft  
**Created**: 2025-09-15  
**Last Updated**: 2025-09-15  
**Version**: 1.0  
**Tags**: `development`, `environment`, `setup`, `troubleshooting`, `python`, `dependencies`

## Purpose

This runbook provides step-by-step procedures for setting up and maintaining development environments for the SISSA Ivy project. It includes Python environment configuration, dependency management, testing setup, and common troubleshooting procedures.

## Prerequisites

Before starting environment setup:
- Access to the repository
- Administrative privileges on development machine
- Internet connection for downloading dependencies
- Basic familiarity with command line operations

## Environment Setup Procedures

### 1. Initial Repository Setup

#### Step 1.1: Clone Repository
```bash
# Clone the repository
git clone https://github.com/your-org/sissa_ivy.git
cd sissa_ivy

# Verify repository structure
ls -la
# Should see: docs/, schema/, scripts/, cogsec/, tests/, requirements.txt, README.md
```

#### Step 1.2: Verify System Prerequisites
```bash
# Check Python version (3.8+ required)
python3 --version
# Should output: Python 3.8.x or higher

# Check git configuration
git config --list | grep user
# Should show your name and email

# Verify curl/wget available (for downloading dependencies)
curl --version && echo "curl available"
wget --version && echo "wget available"
```

### 2. Python Environment Configuration

#### Step 2.1: Create Virtual Environment
```bash
# Create virtual environment using venv
python3 -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Verify activation (prompt should show (.venv))
which python
# Should point to .venv/bin/python

# Upgrade pip to latest version
pip install --upgrade pip
```

#### Step 2.2: Install Dependencies
```bash
# Install all required dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep jsonschema
# Should show: jsonschema==4.23.0

# Install development dependencies (optional)
pip install pytest mypy black pylint

# Create requirements-dev.txt for development dependencies
pip freeze > requirements-dev.txt
```

#### Step 2.3: Validate Installation
```bash
# Test core functionality
python cogsec/collectors/cogsec_probe_linux.py --help
# Should display help text without errors

# Test schema validation
echo '{"host":"test","timestamp":"2025-09-15T10:00:00Z","cpu":50}' | python scripts/validate_linux_probe.py -
# Should show validation errors (incomplete data)

# Run basic probe test
python cogsec/collectors/cogsec_probe_linux.py --pretty
# Should output formatted JSON probe data
```

### 3. Development Tools Configuration

#### Step 3.1: Code Quality Tools Setup
```bash
# Configure pylint
cat > .pylintrc << 'EOF'
[MAIN]
load-plugins=pylint.extensions.mccabe

[MESSAGES CONTROL]
disable=C0111,C0103

[FORMAT]
max-line-length=100

[DESIGN]
max-complexity=10
EOF

# Configure mypy
cat > mypy.ini << 'EOF'
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

[mypy-tests.*]
disallow_untyped_defs = False
EOF

# Configure black formatter
cat > pyproject.toml << 'EOF'
[tool.black]
line-length = 100
target-version = ['py38']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | build
  | dist
)/
'''
EOF
```

#### Step 3.2: Pre-commit Hooks (Optional)
```bash
# Install pre-commit
pip install pre-commit

# Create pre-commit configuration
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.8
  
  - repo: https://github.com/PyCQA/pylint
    rev: v3.0.1
    hooks:
      - id: pylint
        args: [--disable=all, --enable=unused-import]
  
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
EOF

# Install pre-commit hooks
pre-commit install
```

### 4. Testing Environment Setup

#### Step 4.1: Test Framework Configuration
```bash
# Create pytest configuration
cat > pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
EOF

# Create test directory structure
mkdir -p tests/{unit,integration}
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

#### Step 4.2: Basic Test Validation
```bash
# Run existing tests
pytest -v
# Should show test results and pass count

# Run specific test categories
pytest -v -m unit
pytest -v -m integration

# Check test coverage (if coverage installed)
pip install coverage
coverage run -m pytest
coverage report
coverage html  # Generates htmlcov/ directory
```

### 5. IDE and Editor Configuration

#### Step 5.1: VS Code Configuration (Recommended)
```bash
# Create VS Code workspace settings
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        ".coverage": true,
        "htmlcov/": true
    }
}
EOF

# Create launch configuration for debugging
cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run Linux Probe",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/cogsec/collectors/cogsec_probe_linux.py",
            "args": ["--pretty"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "Run Schema Validator",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/scripts/validate_linux_probe.py",
            "args": ["-"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
EOF
```

#### Step 5.2: Alternative Editor Configurations

**Vim/Neovim Configuration**:
```bash
# Add to ~/.vimrc or ~/.config/nvim/init.vim
cat >> ~/.vimrc << 'EOF'
" Python development settings
autocmd FileType python setlocal tabstop=4 shiftwidth=4 expandtab
autocmd FileType python setlocal textwidth=100
autocmd FileType python setlocal colorcolumn=100

" Enable syntax highlighting
syntax on
filetype plugin indent on

" Highlight trailing whitespace
highlight ExtraWhitespace ctermbg=red guibg=red
match ExtraWhitespace /\s\+$/
EOF
```

**Emacs Configuration**:
```bash
# Add to ~/.emacs
cat >> ~/.emacs << 'EOF'
;; Python development settings
(add-hook 'python-mode-hook
          (lambda ()
            (setq tab-width 4
                  python-indent-offset 4
                  python-shell-interpreter "python3"
                  fill-column 100)))

;; Enable line numbers
(global-linum-mode t)

;; Highlight current line
(global-hl-line-mode t)
EOF
```

## Common Troubleshooting Procedures

### 1. Python Environment Issues

#### Problem: "python: command not found"
```bash
# Solution 1: Install Python 3
# Ubuntu/Debian:
sudo apt update && sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL:
sudo yum install python3 python3-pip

# macOS (with Homebrew):
brew install python3

# Solution 2: Check PATH and create alias
which python3
echo 'alias python=python3' >> ~/.bashrc
source ~/.bashrc
```

#### Problem: "ModuleNotFoundError: No module named 'venv'"
```bash
# Solution: Install python3-venv package
# Ubuntu/Debian:
sudo apt install python3-venv

# CentOS/RHEL:
sudo yum install python3-venv

# Alternative: Use virtualenv
pip install virtualenv
virtualenv .venv
```

#### Problem: Virtual environment not activating
```bash
# Check current shell
echo $SHELL

# For bash/zsh:
source .venv/bin/activate

# For fish:
source .venv/bin/activate.fish

# For PowerShell (Windows):
.venv\Scripts\Activate.ps1

# Verify activation
echo $VIRTUAL_ENV
# Should show path to .venv directory
```

### 2. Dependency Installation Issues

#### Problem: "pip install fails with permission errors"
```bash
# Solution 1: Ensure virtual environment is active
source .venv/bin/activate
which pip
# Should point to .venv/bin/pip

# Solution 2: Use --user flag (not recommended for development)
pip install --user package_name

# Solution 3: Fix ownership (if needed)
sudo chown -R $USER:$USER .venv/
```

#### Problem: "Package version conflicts"
```bash
# Solution 1: Check installed packages
pip list | grep conflicting_package

# Solution 2: Create clean environment
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Solution 3: Use pip-tools for dependency resolution
pip install pip-tools
pip-compile requirements.in
pip-sync requirements.txt
```

#### Problem: "jsonschema version mismatch"
```bash
# Check current version
pip show jsonschema

# Force specific version
pip install jsonschema==4.23.0 --force-reinstall

# Verify schema validation works
echo '{}' | python scripts/validate_linux_probe.py -
# Should show validation errors
```

### 3. Testing Framework Issues

#### Problem: "pytest: command not found"
```bash
# Solution 1: Install pytest in virtual environment
source .venv/bin/activate
pip install pytest

# Solution 2: Run as module
python -m pytest tests/

# Solution 3: Add to requirements.txt
echo "pytest>=7.0.0" >> requirements.txt
pip install -r requirements.txt
```

#### Problem: "No tests found" or "import errors in tests"
```bash
# Check test discovery
pytest --collect-only

# Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/

# Check test file naming
ls tests/
# Should have test_*.py files

# Verify __init__.py files exist
find tests/ -name "__init__.py"
# Should show __init__.py in test directories
```

#### Problem: "Tests fail with import errors"
```bash
# Solution 1: Install package in development mode
pip install -e .

# Solution 2: Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Solution 3: Use relative imports in tests
# In test files, use:
# from cogsec.collectors.cogsec_probe_linux import collect_record
```

### 4. Code Quality Tool Issues

#### Problem: "pylint fails with import errors"
```bash
# Solution 1: Install pylint in same environment as code
source .venv/bin/activate
pip install pylint

# Solution 2: Configure pylint to use virtual environment
export PYTHONPATH="${PYTHONPATH}:$(pwd):.venv/lib/python*/site-packages"

# Solution 3: Run pylint with module path
PYTHONPATH=. pylint cogsec/

# Solution 4: Create pylint wrapper script
cat > run_pylint.sh << 'EOF'
#!/bin/bash
source .venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"
pylint "$@"
EOF
chmod +x run_pylint.sh
```

#### Problem: "mypy type checking failures"
```bash
# Check mypy configuration
cat mypy.ini

# Run mypy with verbose output
mypy --verbose cogsec/

# Install type stubs for libraries
pip install types-requests types-setuptools

# Ignore specific errors (temporary)
# Add "# type: ignore" to specific lines
```

### 5. Performance and Resource Issues

#### Problem: "Development environment slow"
```bash
# Check disk space
df -h
# Ensure adequate free space (> 2GB recommended)

# Check memory usage
free -h
# Ensure adequate RAM (> 4GB recommended)

# Optimize virtual environment
# Remove unused packages
pip uninstall -y package_name

# Clear pip cache
pip cache purge

# Clear pytest cache
rm -rf .pytest_cache/
```

#### Problem: "Tests take too long to run"
```bash
# Run specific test categories
pytest -v -m "not slow"

# Parallel test execution
pip install pytest-xdist
pytest -n auto tests/

# Profile test execution
pytest --durations=10 tests/

# Skip integration tests during development
pytest tests/unit/ -v
```

## Environment Validation Checklist

### Pre-Development Checklist
- [ ] Python 3.8+ installed and accessible
- [ ] Virtual environment created and activated
- [ ] All dependencies installed successfully
- [ ] Core functionality tests pass
- [ ] Schema validation works
- [ ] Code quality tools configured

### Development Environment Health Check
```bash
#!/bin/bash
# Save as check_environment.sh

echo "=== Environment Health Check ==="

# Check Python version
echo "Python version:"
python --version

# Check virtual environment
echo "Virtual environment:"
echo $VIRTUAL_ENV

# Check key dependencies
echo "Key dependencies:"
pip show jsonschema | grep Version
pip show pytest | grep Version

# Test core functionality
echo "Testing probe execution:"
timeout 10s python cogsec/collectors/cogsec_probe_linux.py --help > /dev/null && echo "✓ Probe help works" || echo "✗ Probe help failed"

# Test schema validation
echo "Testing schema validation:"
echo '{"host":"test"}' | python scripts/validate_linux_probe.py - > /dev/null 2>&1 && echo "✓ Schema validation works" || echo "✓ Schema validation works (expected failure)"

# Run basic tests
echo "Running tests:"
pytest tests/ -q --tb=no && echo "✓ All tests pass" || echo "✗ Some tests failed"

echo "=== Health Check Complete ==="
```

### Periodic Maintenance Tasks

**Weekly Tasks**:
```bash
# Update dependencies
pip list --outdated
# Review and update as needed

# Clean up cache
pip cache purge
rm -rf .pytest_cache/
rm -rf __pycache__/
find . -name "*.pyc" -delete

# Run full test suite
pytest tests/ -v
```

**Monthly Tasks**:
```bash
# Security audit of dependencies
pip install safety
safety check

# Update development tools
pip install --upgrade pip pytest mypy black pylint

# Review and update .gitignore
git status --ignored
# Add any new patterns as needed

# Backup important configurations
cp .vscode/settings.json .vscode/settings.json.bak
cp requirements.txt requirements.txt.bak
```

## Emergency Recovery Procedures

### Complete Environment Reset
```bash
# Backup important files
cp requirements.txt requirements.txt.backup
cp -r .vscode/ .vscode.backup/

# Remove virtual environment
deactivate
rm -rf .venv/

# Clean repository (keep changes)
git clean -fd

# Recreate environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt.backup

# Restore configurations
cp -r .vscode.backup/ .vscode/

# Validate environment
bash check_environment.sh
```

### Dependency Corruption Recovery
```bash
# Save current state
pip freeze > current_packages.txt

# Remove problematic packages
pip uninstall -y $(pip freeze | cut -d= -f1)

# Reinstall from clean requirements
pip install -r requirements.txt

# Compare package lists
diff current_packages.txt <(pip freeze)
```

## Related Documents

- **SOP-002**: Repository Governance and Change Management
- **KB-001**: Schema Validation Implementation Patterns
- **KB-002**: War Room UI Development Patterns
- **RB-001**: Quick Fix Identification and Patch Application

## Support and Escalation

### First-Level Support
1. Check this runbook for common issues
2. Search project documentation
3. Check GitHub issues for similar problems
4. Review recent changes that might have caused issues

### Escalation Procedures
- **Development Environment Issues**: Contact Technical Lead
- **Infrastructure Problems**: Contact DevOps Team
- **Security Concerns**: Follow security incident procedures
- **Urgent Blockers**: Use emergency contact procedures

---

**Document Owner**: Development Team  
**Emergency Contact**: Technical Lead  
**Last Updated**: 2025-09-15  
**Next Review Date**: 2025-12-15  
**Usage Frequency**: As needed for new developers and troubleshooting