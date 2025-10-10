# GPG Commit Signing Guide

> Make your commits look official with that verified badge ✅

## Why Sign Commits?

**TL;DR:** It proves YOU wrote the code, not some impersonator.

**Real benefits:**
- ✅ Verified badge on GitHub (looks professional)
- ✅ Proves commits came from you
- ✅ Required by many open source projects
- ✅ Prevents commit impersonation
- ✅ Industry best practice for security

**Note:** This is **optional** for solo developers, but recommended once your project gets traction.

---

## Quick Setup (macOS/Linux)

### 1. Install GPG

**macOS:**
```bash
brew install gnupg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install gnupg
```

### 2. Generate GPG Key

```bash
gpg --full-generate-key
```

**Choose these options:**
- Key type: **RSA and RSA** (option 1)
- Key size: **4096** bits
- Expiration: **0** (never expires) or **2y** (2 years - more secure)
- Real name: **Your actual name** (must match GitHub)
- Email: **Your GitHub email** (very important!)
- Passphrase: **Strong password** (you'll need this every commit)

### 3. Get Your GPG Key ID

```bash
gpg --list-secret-keys --keyid-format=long
```

Output will look like:
```
sec   rsa4096/3AA5C34371567BD2 2025-10-10 [SC]
      1234567890ABCDEF1234567890ABCDEF12345678
uid           [ultimate] Your Name <your.email@example.com>
ssb   rsa4096/4BB6D45482678BE3 2025-10-10 [E]
```

Your key ID is: **3AA5C34371567BD2** (the part after `rsa4096/`)

### 4. Export Public Key

```bash
gpg --armor --export 3AA5C34371567BD2
```

This outputs your public key. Copy the ENTIRE output (including `-----BEGIN PGP PUBLIC KEY BLOCK-----` and `-----END PGP PUBLIC KEY BLOCK-----`).

### 5. Add Key to GitHub

1. Go to: https://github.com/settings/keys
2. Click **"New GPG key"**
3. Paste your public key
4. Click **"Add GPG key"**

### 6. Configure Git

```bash
# Set your GPG key
git config --global user.signingkey 3AA5C34371567BD2

# Sign all commits by default
git config --global commit.gpgsign true

# Sign all tags by default
git config --global tag.gpgsign true
```

### 7. Test It!

```bash
echo "test" > test.txt
git add test.txt
git commit -S -m "test: GPG signing"
```

If it asks for your passphrase, you're good! The `-S` flag is automatic now.

Push and check GitHub - you should see a **Verified** badge! ✅

---

## Troubleshooting

### "gpg: signing failed: Inappropriate ioctl for device"

**macOS fix:**
```bash
echo 'export GPG_TTY=$(tty)' >> ~/.zshrc
source ~/.zshrc
```

**Linux fix:**
```bash
echo 'export GPG_TTY=$(tty)' >> ~/.bashrc
source ~/.bashrc
```

### "gpg: signing failed: No secret key"

Your key ID is wrong. List keys again:
```bash
gpg --list-secret-keys --keyid-format=long
```

### "error: gpg failed to sign the data"

Start the GPG agent:
```bash
gpgconf --kill gpg-agent
gpg-agent --daemon
```

### "Passphrase prompt not showing"

Install pinentry:
```bash
# macOS
brew install pinentry-mac
echo "pinentry-program $(which pinentry-mac)" > ~/.gnupg/gpg-agent.conf
gpgconf --kill gpg-agent
```

### "Commits still show unverified"

Check your email:
```bash
git config user.email
```

Must match EXACTLY with:
- Your GPG key email
- Your GitHub account email

Fix it:
```bash
git config --global user.email "your.email@example.com"
```

---

## Advanced: Key Management

### Backup Your Key (IMPORTANT!)

```bash
# Export private key (keep this VERY safe!)
gpg --export-secret-keys --armor 3AA5C34371567BD2 > gpg-private-key.asc

# Store in password manager or encrypted backup
```

### Restore Key on New Machine

```bash
gpg --import gpg-private-key.asc
```

### Extend Expiration

If your key expires:
```bash
gpg --edit-key 3AA5C34371567BD2
> expire
> 2y
> save
```

Then re-export and update on GitHub.

### Revoke Compromised Key

If your private key is compromised:
```bash
gpg --gen-revoke 3AA5C34371567BD2 > revoke.asc
gpg --import revoke.asc
gpg --send-keys 3AA5C34371567BD2
```

Then generate a new key and update GitHub.

---

## Daily Use

### Normal Commit (Auto-signed)
```bash
git commit -m "feat: add awesome feature"
# GPG signs automatically
```

### Amend Commit
```bash
git commit --amend
# Still signed!
```

### Rebase
```bash
git rebase -i HEAD~3
# All commits stay signed
```

### Skip Signing (Emergency Only)
```bash
git commit --no-gpg-sign -m "emergency: fix production"
# NOT RECOMMENDED
```

---

## Why This Matters for Open Source

**Scenario: Malicious Actor**

Without signing:
1. Attacker clones your repo
2. Sets their name/email to yours: `git config user.name "Your Name"`
3. Makes malicious commits
4. They look like they came from you
5. Damage to your reputation

With signing:
1. Attacker can fake name/email
2. **But they can't sign with YOUR private key**
3. GitHub shows "Unverified" ❌
4. Everyone knows it's fake
5. Your reputation is protected

---

## Best Practices

1. **Never share your private key** - It's like your password
2. **Use a strong passphrase** - Prevents key theft
3. **Backup your key securely** - Encrypted backup or password manager
4. **Set expiration dates** - 2 years is good balance
5. **Keep GPG updated** - `brew upgrade gnupg` regularly
6. **Add subkeys for different machines** - Advanced but more secure

---

## Resources

- [GitHub GPG Docs](https://docs.github.com/en/authentication/managing-commit-signature-verification)
- [GPG Best Practices](https://riseup.net/en/security/message-security/openpgp/gpg-best-practices)
- [GPG Cheat Sheet](https://github.com/NicoHood/gpg-remailer/wiki/GPG-Cheat-Sheet)

---

**Remember:** This is optional for personal projects, but once you're accepting contributions or building something serious, it becomes important. Start the habit early!