# Repository Transfer Scripts

This directory contains scripts for transferring GitHub repositories from SissaIvy to mrobot787.

## Scripts

### PowerShell Script: `transfer-repos.ps1`

A comprehensive PowerShell script that uses the GitHub REST API to transfer repositories with advanced features:

- **Name conflict detection**: Automatically renames repositories if they already exist in the target account
- **Transfer confirmation**: Polls the API to confirm successful transfers
- **Error handling**: Graceful handling of API errors and timeouts
- **Progress reporting**: Shows transfer status for each repository

#### Prerequisites
1. Create a Personal Access Token (classic) for SissaIvy with `repo` scope
2. Edit the script and replace `<SISSAIVY_PAT>` with your actual token

#### Usage
```powershell
# Run with ephemeral execution policy bypass
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\transfer-repos.ps1
```

#### Features
- Handles name conflicts by appending `-from-SissaIvy` suffix
- Waits up to 60 seconds (20 attempts × 3 seconds) for transfer confirmation
- Uses GitHub API v2022-11-28 for compatibility

### Bash Script: `transfer-repos.sh`

A simpler alternative using the GitHub CLI (gh) tool:

#### Prerequisites
1. Install GitHub CLI: https://cli.github.com/
2. Authenticate: `gh auth login`

#### Usage
```bash
./scripts/transfer-repos.sh
```

## Target Repositories

The following repositories will be transferred from SissaIvy to mrobot787:

1. **Episodic-Memory-System-Python-** - [Source](https://github.com/SissaIvy/Episodic-Memory-System-Python-)
2. **nlp-landing** - [Source](https://github.com/SissaIvy/nlp-landing)

## Important Notes

- **Transfer acceptance**: Repository transfers may require acceptance by the target account owner (mrobot787)
- **Email notifications**: GitHub will send email notifications about pending transfers
- **Permissions**: Both scripts require appropriate permissions on the source repositories
- **Rollback**: Repository transfers can be reversed if needed before acceptance

## References

- [GitHub Documentation: Transferring a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository)
- [GitHub REST API: Repository transfers](https://docs.github.com/en/rest/repos/repos#transfer-a-repository)
- [GitHub CLI: Repository transfer](https://cli.github.com/manual/gh_repo_transfer)