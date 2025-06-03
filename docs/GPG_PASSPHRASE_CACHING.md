# GPG Passphrase Caching Guide

## Overview

When using GPG to sign commits, you'll be prompted for your passphrase on each commit by default. This guide shows how to configure GPG to cache your passphrase so you only need to enter it once per session.

## Configuration

### 1. GPG Agent Configuration

Create or update `~/.gnupg/gpg-agent.conf`:

```bash
# Cache passphrase for 1 hour (3600 seconds)
default-cache-ttl 3600

# Maximum cache time 24 hours
max-cache-ttl 86400

# Enable pinentry mode for macOS
pinentry-program /opt/homebrew/bin/pinentry
```

### 2. Apply Configuration

Restart the GPG agent:

```bash
gpgconf --kill gpg-agent
gpg-agent --daemon
```

### 3. Set Environment Variable

Add to your shell configuration (`~/.zshrc` or `~/.bashrc`):

```bash
export GPG_TTY=$(tty)
```

## Cache Duration Settings

- `default-cache-ttl`: How long (in seconds) to cache the passphrase after each use
  - Default: 600 (10 minutes)
  - Recommended: 3600 (1 hour)
- `max-cache-ttl`: Maximum time (in seconds) to cache the passphrase regardless of use
  - Default: 7200 (2 hours)
  - Recommended: 86400 (24 hours)

## Testing

After configuration:

1. Make a commit - you'll be prompted for passphrase
2. Make another commit - no prompt should appear
3. The passphrase will remain cached for the configured duration

## Troubleshooting

### Still Being Prompted?

1. Ensure GPG agent is running:

   ```bash
   gpg-agent --daemon
   ```

2. Check if GPG_TTY is set:

   ```bash
   echo $GPG_TTY
   ```

3. Verify cache settings:
   ```bash
   gpgconf --list-options gpg-agent | grep cache
   ```

### Clear Cached Passphrase

To manually clear the cache:

```bash
gpgconf --reload gpg-agent
```

## Security Considerations

- Longer cache times are more convenient but less secure
- On shared systems, use shorter cache times
- The cache is cleared on system restart
- Consider your threat model when setting cache duration

## Platform-Specific Notes

### macOS

- Use `pinentry-mac` if available (install with `brew install pinentry-mac`)
- Otherwise use the default `pinentry`

### Linux

- Usually works out of the box
- May need to install `pinentry-gtk2` or `pinentry-qt`

### Windows

- Use `pinentry-w32` on Windows systems
- Ensure GPG4Win is properly installed
