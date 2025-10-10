# Branch Protection Setup Guide

> Protecting `main` branch so future you doesn't accidentally break production

## Why This Matters

**Without protection:** You can accidentally `git push` directly to main and break everything.

**With protection:** GitHub forces you to use pull requests, even when you're solo.

**Result:** Professional workflow, clean history, always-deployable main branch.

---

## Quick Setup (2 Minutes)

### Step 1: Navigate to Settings

1. Go to: https://github.com/MatthewJamisonJS/claude-on-the-go
2. Click **Settings** tab (top navigation)
3. Click **Branches** in left sidebar (under "Code and automation")
4. Click **Add branch protection rule**

### Step 2: Set Branch Name

**Branch name pattern:** `main`

(Just type `main` - no wildcards needed)

### Step 3: Configure Protection Rules

**Check these boxes:**

#### Protect Matching Branches

- ☑️ **Require a pull request before merging**
  - ☐ Require approvals (LEAVE UNCHECKED - you're solo!)
  - ☑️ Dismiss stale pull request approvals when new commits are pushed
  - ☐ Require review from Code Owners (skip for now)

- ☑️ **Require status checks to pass before merging**
  - ☑️ Require branches to be up to date before merging
  - ⚠️ **Note:** No status checks to add yet (we'll add when GitHub Actions is set up)

- ☑️ **Require conversation resolution before merging**

- ☑️ **Require linear history** (keeps main clean with squash merges)

- ☐ Require signed commits (optional - skip for now)

#### Rules Applied to Everyone

- ☑️ **Do not allow bypassing the above settings**
  - ☑️ **Include administrators** ← **CRITICAL!** This protects YOU from YOU

#### Auto-Enabled (Good!)

- ☑️ Prevent force pushes (automatically enabled)
- ☑️ Prevent branch deletion (automatically enabled)

### Step 4: Save

Click **Create** at the bottom.

---

## What Just Happened?

### Before Protection

```bash
# This would work (BAD!)
git checkout main
git add broken_code.py
git commit -m "oops"
git push origin main  # ← GitHub would accept this 😱
```

### After Protection

```bash
# This gets REJECTED by GitHub
git checkout main
git add broken_code.py
git commit -m "oops"
git push origin main  # ← GitHub says: "Nope! Use a PR!" 🛡️

# Error message you'll see:
# remote: error: GH006: Protected branch update failed
# remote: error: Required status checks must pass before merging
# remote: error: At least 1 approving review is required
```

### New Workflow (FORCED!)

```bash
# 1. Create feature branch
git checkout -b feature/fix-thing

# 2. Make changes and commit
git add fixed_code.py
git commit -m "fix: actually works now"

# 3. Push feature branch
git push -u origin feature/fix-thing

# 4. Go to GitHub and create Pull Request

# 5. Review your own code (seriously!)

# 6. Click "Squash and merge"

# 7. Main is updated via PR ✅
```

---

## GitHub Actions CI/CD Setup (DONE! ✅)

**Good news:** The CI/CD workflows are already created and ready to use!

### What's Configured

We have two workflows running on every PR:

**1. `.github/workflows/ci.yml` - Main CI Pipeline**
- Job name: `automated_test` (this is what the status check requires)
- Runs: pytest, mypy, black, isort
- Currently non-blocking (warnings only) during setup phase

**2. `.github/workflows/pr-checks.yml` - Quality Checks**
- Code linting (flake8)
- Security scanning (bandit)
- Dependency vulnerabilities (safety)
- Code complexity analysis (radon)
- PR size warnings
- Commit message format validation

### How to Enable Status Checks

**After your first PR is merged** (which will register the workflows with GitHub):

1. Go to: Settings → Branches
2. Click **Edit** on your main branch rule
3. Check ☑️ **"Require status checks to pass before merging"**
4. In the search box, type: `automated_test`
5. Click the checkbox next to it
6. Click **Save changes**

Now PRs **can't merge** unless CI passes! 🎯

### Viewing CI Results

Once you create your first PR:
- GitHub Actions will automatically run
- You'll see status badges on the PR
- Click "Details" to see full logs
- Green checkmark ✅ = ready to merge
- Red X ❌ = needs fixing

### Adding More Status Checks (Optional)

You can also require the quality checks:
- `code-quality` - Linting and security
- `pr-size-check` - Warns about large PRs
- `commit-message-check` - Validates conventional commits

---

## Solo Developer FAQs

### Q: Why can't I approve my own PRs?

**A:** Because you're the repository admin. GitHub lets admins approve their own PRs, which defeats the purpose. Instead, we rely on **status checks** (automated tests) to ensure quality.

**Solution:** Don't require approvals, require status checks instead.

### Q: What if I need to push directly to main in an emergency?

**A:** You have two options:

**Option 1: Temporarily disable protection (NOT RECOMMENDED)**
1. Settings → Branches → Edit rule
2. Uncheck "Include administrators"
3. Make your emergency push
4. **IMMEDIATELY** re-enable "Include administrators"

**Option 2: Use a quick PR (RECOMMENDED)**
```bash
git checkout -b hotfix/critical-bug
git commit -m "fix: critical production bug"
git push -u origin hotfix/critical-bug
# Create PR, merge immediately (no wait for review)
```

### Q: Does this slow me down?

**A:** Slightly (~30 seconds per merge), but you gain:
- ✅ Forced code review (even self-review catches bugs)
- ✅ Clean git history (easier to debug)
- ✅ Professional presentation (for employers/investors)
- ✅ Safety net (can't accidentally break main)

**Trade-off is worth it.**

### Q: Can I still delete my feature branches?

**A:** Yes! Branch protection only applies to `main`. You can do whatever you want with feature branches:
- Delete them after merging ✅
- Force push to them ✅
- Rebase them ✅
- Squash commits ✅

### Q: What about `dependabot` or GitHub Actions pushing to main?

**A:** GitHub Actions with proper permissions can bypass some restrictions. Configure this when you set up CI/CD.

---

## Verification

After setting up protection, test it:

### Test 1: Try to push directly to main

```bash
git checkout main
echo "test" > test.txt
git add test.txt
git commit -m "test: should fail"
git push origin main
```

**Expected result:**
```
remote: error: GH006: Protected branch update failed for refs/heads/main
```

✅ **If you see this error, protection is working!**

### Test 2: Try the PR workflow

```bash
# Create feature branch
git checkout -b test/branch-protection
echo "test" > test.txt
git add test.txt
git commit -m "test: verifying PR workflow"
git push -u origin test/branch-protection
```

Then:
1. Go to GitHub
2. Click "Compare & pull request"
3. Create the PR
4. Merge it
5. Verify it worked

✅ **If you can merge via PR, it's working correctly!**

### Test 3: Verify you can't bypass

Try to bypass protection as admin:

```bash
git checkout main
git pull
echo "bypass" > bypass.txt
git add bypass.txt
git commit -m "test: bypass attempt"
git push origin main
```

**Expected result:** Should FAIL if "Include administrators" is checked.

**If it succeeds:** Go back and enable "Include administrators"!

---

## Current Status

- [x] **DONE:** Created GitHub Actions CI/CD workflows
- [x] **DONE:** Documented branch protection setup process
- [x] **DONE:** Hardened CI with caching, timeouts, and strict checks
- [x] **DONE:** Added security automation (Dependabot, CodeQL, etc.)
- [ ] **TODO:** Configure branch protection on GitHub (manual setup required)
  - [ ] Enable "Require status checks to pass"
  - [ ] Add status checks: automated_test, code-quality, commit-message-check
  - [ ] Enable "Include administrators" ← CRITICAL!
- [ ] **TODO:** Test direct push to main (should fail)
- [ ] **TODO:** Test PR workflow (should succeed)
- [ ] **TODO:** Optional: Set up GPG commit signing (see docs/GPG_SIGNING_GUIDE.md)

---

## When Configured, Update This Checklist

Once branch protection is active, mark these done:

**Basic Protection (Now):**
- [ ] Require pull requests
- [ ] Require linear history
- [ ] Include administrators
- [ ] Test that direct pushes fail

**Advanced Protection (Later):**
- [ ] Add status check: `test` (pytest)
- [ ] Add status check: `type-check` (mypy)
- [ ] Add status check: `lint` (black, isort)
- [ ] Add status check: `build` (when you have builds)
- [ ] Add CODEOWNERS file (when you have a team)

---

## Resources

- [GitHub Docs: Protected Branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [GitHub Docs: Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)
- [Best Practices: Solo Developer Branch Protection](https://github.com/orgs/community/discussions/23727)

---

## Pro Tips

1. **Screenshot your settings** - For future reference when setting up new repos

2. **Test immediately** - Don't assume it's working, verify with real pushes

3. **Document exceptions** - If you bypass protection, note why in commit message

4. **Review your own PRs** - Take 60 seconds to read the diff, you'll catch bugs

5. **Use descriptive PR titles** - They show up in `git log` on main branch

6. **Celebrate the friction** - That "annoying" PR step is saving you from bugs

7. **GPG signing is optional** - See [docs/GPG_SIGNING_GUIDE.md](GPG_SIGNING_GUIDE.md) for setup. Nice to have but not required for solo projects.

---

**Remember:** Branch protection isn't about distrust. It's about having a professional workflow that scales from 1 developer to 100 developers. Start good habits now.

**Next step:** Go to GitHub and configure it! Takes 2 minutes, saves hours of debugging later.
