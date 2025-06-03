# GPG Indefinite Passphrase Cache Setup

## Configuration Applied

Your GPG is now configured to cache your passphrase indefinitely on this machine.

### Settings:

- **Cache Duration**: 10 years (315,360,000 seconds)
- **Passphrase Entry**: Only required once after system restart
- **Location**: `~/.gnupg/gpg-agent.conf`

### Current Configuration:

```bash
# Cache passphrase indefinitely (10 years in seconds)
default-cache-ttl 315360000

# Maximum cache time 10 years
max-cache-ttl 315360000

# Enable pinentry mode for macOS
pinentry-program /opt/homebrew/bin/pinentry

# Don't ask for confirmation
allow-loopback-pinentry
```

### How It Works:

1. Enter passphrase once when first signing after boot
2. Passphrase remains cached for 10 years
3. No more passphrase prompts during normal use

### To Revert to Secure Settings:

```bash
# Edit ~/.gnupg/gpg-agent.conf
default-cache-ttl 3600      # 1 hour
max-cache-ttl 86400        # 24 hours

# Restart agent
gpgconf --kill gpg-agent
```

### Security Note:

⚠️ This configuration trades security for convenience. Only use on:

- Personal development machines
- Physically secure environments
- Systems with full disk encryption

The passphrase will only be requested:

- After system restart
- After manually clearing the cache
- After 10 years (effectively never)
