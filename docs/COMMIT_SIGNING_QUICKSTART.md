# Quick Start: Enable Commit Signing

## 1. Install GPG (if not already installed)

### macOS:

```bash
brew install gnupg
```

### Linux:

```bash
# Ubuntu/Debian
sudo apt-get install gnupg

# Fedora
sudo dnf install gnupg2
```

## 2. Run the Setup Script

We've created a script to automate the setup:

```bash
./scripts/setup-commit-signing.sh
```

This script will:

- ✅ Check if GPG is installed
- ✅ Help you create or select a GPG key
- ✅ Export your public key for GitHub
- ✅ Configure Git to sign all commits
- ✅ Set up your terminal environment

## 3. Add Your GPG Key to GitHub

1. The script will show your public key
2. Copy it (including BEGIN/END lines)
3. Go to [GitHub GPG Settings](https://github.com/settings/keys)
4. Click "New GPG key" and paste

## 4. Test It Works

```bash
# Make a test commit
echo "test" > test-signing.txt
git add test-signing.txt
git commit -m "test: verify commit signing"

# Check if it's signed
git log --show-signature -1
```

You should see "Good signature" in the output.

## 5. Enable Branch Protection (Optional)

To require signed commits on protected branches:

```bash
./scripts/enable-signed-commits-protection.sh
```

## Troubleshooting

If commits aren't being signed:

1. Restart your terminal
2. Run: `export GPG_TTY=$(tty)`
3. Check your key: `gpg --list-secret-keys`
4. Verify Git config: `git config --global --list | grep sign`

For detailed instructions, see [docs/COMMIT_SIGNING_SETUP.md](docs/COMMIT_SIGNING_SETUP.md)
