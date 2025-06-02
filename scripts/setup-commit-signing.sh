#!/bin/bash

# Tastory Commit Signing Setup Script
# This script helps you set up GPG commit signing

set -e

echo "🔐 Tastory Commit Signing Setup"
echo "==============================="
echo ""

# Check if GPG is installed
if ! command -v gpg &> /dev/null; then
    echo "❌ GPG is not installed!"
    echo ""
    echo "Please install GPG first:"
    echo "  macOS:    brew install gnupg"
    echo "  Ubuntu:   sudo apt-get install gnupg"
    echo "  Fedora:   sudo dnf install gnupg2"
    echo ""
    exit 1
fi

echo "✅ GPG is installed: $(gpg --version | head -n 1)"
echo ""

# Check for existing GPG keys
echo "🔍 Checking for existing GPG keys..."
EXISTING_KEYS=$(gpg --list-secret-keys --keyid-format=long 2>/dev/null | grep -E "^sec" || true)

if [ -n "$EXISTING_KEYS" ]; then
    echo "Found existing GPG keys:"
    gpg --list-secret-keys --keyid-format=long
    echo ""
    read -p "Do you want to use an existing key? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your GPG key ID (the part after rsa4096/): " KEY_ID
    else
        GENERATE_NEW=true
    fi
else
    echo "No existing GPG keys found."
    GENERATE_NEW=true
fi

# Generate new key if needed
if [ "$GENERATE_NEW" = true ]; then
    echo ""
    echo "📝 Generating new GPG key..."
    echo "Please follow the prompts:"
    echo "  - Key type: RSA and RSA (option 1)"
    echo "  - Key size: 4096"
    echo "  - Expiration: 0 (no expiration) or your preference"
    echo "  - Use your real name and GitHub email"
    echo ""
    
    gpg --full-generate-key
    
    # Get the newly created key ID
    echo ""
    echo "🔍 Finding your new key ID..."
    KEY_ID=$(gpg --list-secret-keys --keyid-format=long | grep -E "^sec" | tail -1 | awk -F'/' '{print $2}' | awk '{print $1}')
    echo "Your key ID is: $KEY_ID"
fi

# Export public key
echo ""
echo "📤 Exporting your public key..."
PUBLIC_KEY=$(gpg --armor --export $KEY_ID)

echo ""
echo "Your GPG public key:"
echo "===================="
echo "$PUBLIC_KEY"
echo "===================="
echo ""
echo "📋 Copy the above key (including BEGIN/END lines) and:"
echo "   1. Go to https://github.com/settings/keys"
echo "   2. Click 'New GPG key'"
echo "   3. Paste the key and save"
echo ""
read -p "Press Enter when you've added the key to GitHub..."

# Configure Git
echo ""
echo "⚙️  Configuring Git to use GPG signing..."

# Get current Git user info
GIT_USER=$(git config --global user.name || echo "")
GIT_EMAIL=$(git config --global user.email || echo "")

if [ -z "$GIT_USER" ] || [ -z "$GIT_EMAIL" ]; then
    echo "Git user info not configured. Please set it up first:"
    echo "  git config --global user.name \"Your Name\""
    echo "  git config --global user.email \"your.email@example.com\""
    exit 1
fi

# Set up Git signing
git config --global user.signingkey $KEY_ID
git config --global commit.gpgsign true
git config --global tag.gpgsign true

echo "✅ Git configured to sign commits with key: $KEY_ID"

# Configure GPG TTY
echo ""
echo "⚙️  Configuring GPG TTY..."

SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "export GPG_TTY" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# GPG TTY for commit signing" >> "$SHELL_RC"
        echo "export GPG_TTY=\$(tty)" >> "$SHELL_RC"
        echo "✅ Added GPG_TTY to $SHELL_RC"
    else
        echo "✅ GPG_TTY already configured in $SHELL_RC"
    fi
fi

# Set GPG_TTY for current session
export GPG_TTY=$(tty)

# macOS specific config
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo ""
    echo "🍎 Applying macOS-specific configurations..."
    mkdir -p ~/.gnupg
    echo "pinentry-mode loopback" >> ~/.gnupg/gpg.conf
    echo "✅ Configured pinentry mode for macOS"
fi

# Test signing
echo ""
echo "🧪 Testing GPG signing..."
echo "test" | gpg --clearsign > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ GPG signing works!"
else
    echo "❌ GPG signing test failed. You may need to restart your terminal."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Restart your terminal or run: export GPG_TTY=\$(tty)"
echo "2. Make a test commit to verify signing works"
echo "3. Your commits will now be signed automatically"
echo ""
echo "To verify a commit is signed, use:"
echo "  git log --show-signature -1"
echo ""
echo "For more info, see: docs/COMMIT_SIGNING_SETUP.md" 