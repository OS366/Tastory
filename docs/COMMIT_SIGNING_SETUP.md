# Commit Signing Setup Guide

This guide will help you set up GPG commit signing for the Tastory project to ensure all commits are verified.

## Prerequisites

### 1. Install GPG

#### macOS

```bash
# Using Homebrew
brew install gnupg

# Verify installation
gpg --version
```

#### Linux

```bash
# Ubuntu/Debian
sudo apt-get install gnupg

# Fedora
sudo dnf install gnupg2
```

#### Windows

Download from: https://www.gnupg.org/download/

## Setup Process

### 1. Generate a GPG Key

```bash
# Generate a new GPG key pair
gpg --full-generate-key
```

Choose:

- Key type: RSA and RSA (default)
- Key size: 4096 bits
- Expiration: 0 (does not expire) or your preference
- Enter your real name and email (must match your GitHub email)

### 2. List Your GPG Keys

```bash
# List GPG keys with long format
gpg --list-secret-keys --keyid-format=long
```

Example output:

```
sec   rsa4096/3AA5C34371567BD2 2024-06-01 [SC]
      ABCDEF1234567890ABCDEF1234567890ABCDEF12
uid                 [ultimate] Your Name <your.email@example.com>
```

The GPG key ID is the part after `rsa4096/` (in this example: `3AA5C34371567BD2`)

### 3. Export Your GPG Public Key

```bash
# Export public key (replace with your key ID)
gpg --armor --export 3AA5C34371567BD2
```

Copy the output including:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
...
-----END PGP PUBLIC KEY BLOCK-----
```

### 4. Add GPG Key to GitHub

1. Go to GitHub Settings → SSH and GPG keys
2. Click "New GPG key"
3. Paste your public key
4. Click "Add GPG key"

### 5. Configure Git to Sign Commits

```bash
# Set your GPG signing key
git config --global user.signingkey 3AA5C34371567BD2

# Enable commit signing by default
git config --global commit.gpgsign true

# Optional: Enable tag signing
git config --global tag.gpgsign true
```

### 6. Configure GPG for Terminal

```bash
# Add to your ~/.bashrc or ~/.zshrc
export GPG_TTY=$(tty)

# For macOS, you might also need:
echo "pinentry-mode loopback" >> ~/.gnupg/gpg.conf
```

## Repository Configuration

### Enable Signed Commits Only (Branch Protection)

1. Go to Repository Settings → Branches
2. Edit protection rules for main branches
3. Check "Require signed commits"

### Add Verification Workflow

Create `.github/workflows/verify-commits.yml`:

```yaml
name: Verify Commits

on:
  pull_request:
    types: [opened, synchronize]
  push:
    branches: [main, development, stable]

jobs:
  verify-commits:
    name: Verify Commit Signatures
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Verify commit signatures
        run: |
          # Get commits in this PR or push
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            COMMITS=$(git rev-list ${{ github.event.pull_request.base.sha }}..${{ github.event.pull_request.head.sha }})
          else
            COMMITS=$(git rev-list ${{ github.event.before }}..${{ github.event.after }})
          fi

          # Check each commit
          for commit in $COMMITS; do
            if ! git verify-commit $commit &>/dev/null; then
              echo "❌ Unsigned commit detected: $commit"
              git log --format='%h %s' -n 1 $commit
              exit 1
            fi
          done

          echo "✅ All commits are signed and verified!"
```

## Testing Your Setup

### Test Signing

```bash
# Make a test commit
echo "test" > test-signing.txt
git add test-signing.txt
git commit -m "test: verify commit signing"

# Verify the commit was signed
git log --show-signature -1
```

You should see:

```
gpg: Signature made [date]
gpg: Good signature from "Your Name <your.email@example.com>"
```

### View Commits on GitHub

Signed commits will show a "Verified" badge on GitHub.

## Troubleshooting

### GPG Asking for Passphrase Too Often

```bash
# Configure GPG agent timeout (in seconds)
echo "default-cache-ttl 3600" >> ~/.gnupg/gpg-agent.conf
echo "max-cache-ttl 86400" >> ~/.gnupg/gpg-agent.conf

# Restart GPG agent
gpgconf --kill gpg-agent
```

### "Cannot open tty" Error

```bash
export GPG_TTY=$(tty)
```

### Signing Failed

```bash
# Test GPG
echo "test" | gpg --clearsign

# If that fails, check GPG agent
gpg-agent --daemon
```

## Team Setup

For team members:

1. Each developer must set up their own GPG key
2. Add their GPG key to GitHub
3. Configure local Git to sign commits
4. Project maintainers should enable branch protection

## CI/CD Considerations

- GitHub Actions commits (like from bots) won't be signed
- Consider using a bot GPG key for automated commits
- Or allow unsigned commits from specific GitHub Apps

## References

- [GitHub GPG Documentation](https://docs.github.com/en/authentication/managing-commit-signature-verification)
- [Git Signing Documentation](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)
- [GPG Best Practices](https://riseup.net/en/security/message-security/openpgp/best-practices)
