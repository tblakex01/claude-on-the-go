# Git Workflow Guide

> How we ship clean code without looking like amateurs on GitHub

## Philosophy

**Main branch is sacred.** It should always be deployable, always working, always ready to show to potential employers/investors/your mom.

We achieve this through:
1. **Feature branches** for all changes (no exceptions)
2. **Pull requests** for code review (even solo developers benefit)
3. **Automated checks** before every commit (pre-commit hooks)
4. **Conventional commits** for clear history (future you will thank present you)

---

## Daily Workflow

### Starting Your Day

```bash
# 1. Update main branch
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-awesome-feature

# 3. Make magic happen
# ... code code code ...
```

### While Working

```bash
# Commit early and often (small commits are beautiful)
git add file1.py file2.py
git commit -m "feat(core): add session timeout handling"

# More changes
git add tests/test_session.py
git commit -m "test(core): add tests for session timeout"

# Keep going...
git add docs/README.md
git commit -m "docs: document session timeout config"
```

**Pro tips:**
- Commit every logical change separately
- Each commit should pass tests
- If you can't describe the commit in one line, it's too big

### Before Pushing

```bash
# Run the checks (pre-commit hook does this automatically)
pytest
mypy core/ server/ integrations/
black --check .
isort --check .

# All good? Push it!
git push -u origin feature/your-awesome-feature
```

### Creating a Pull Request

1. Go to GitHub
2. Click "Compare & pull request"
3. Write a description:
   ```markdown
   ## What
   Adds session timeout to prevent zombie sessions

   ## Why
   Users were leaving sessions open indefinitely, causing memory leaks

   ## How
   - Added timeout config to Config class
   - SessionStore now tracks last activity
   - Background task cleans up expired sessions every 5 minutes

   ## Testing
   - [x] Added unit tests for timeout logic
   - [x] Tested manually with 1-minute timeout
   - [x] Verified old sessions get cleaned up

   Closes #42
   ```
4. Request review (or self-review if solo)
5. Wait for CI to pass
6. Squash merge to main
7. Delete the branch
8. Celebrate 🎉

---

## Branch Naming

Be descriptive. Future you should know what this branch is about from the name.

**Good:**
- `feature/add-push-notifications`
- `fix/websocket-reconnection-race-condition`
- `refactor/simplify-pty-manager`
- `docs/add-api-reference`

**Bad:**
- `test` (test what?)
- `fix-bug` (which bug?)
- `updates` (what updates?)
- `asdf` (are you okay?)

**Convention:**
```
<type>/<description>

Types:
  feature/  - New features
  fix/      - Bug fixes
  refactor/ - Code refactoring
  docs/     - Documentation
  test/     - Adding tests
  chore/    - Maintenance
```

---

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/) because we're professionals (mostly).

### Format

```
<type>(<scope>): <short description>

[optional body explaining what and why]

[optional footer with issue references]
```

### Types

- `feat:` New feature (shows up in changelog)
- `fix:` Bug fix (shows up in changelog)
- `docs:` Documentation only
- `style:` Code style (formatting, etc)
- `refactor:` Code restructuring
- `perf:` Performance improvement
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### Scopes

- `core` - PTY manager, session store, config
- `server` - FastAPI WebSocket + REST API
- `client` - Web client, PWA
- `integrations` - Notifications, Tailscale, QR
- `cli` - Command-line interface

### Examples

**Simple feature:**
```
feat(server): add REST endpoint for session list
```

**Bug fix with context:**
```
fix(core): resolve memory leak in PTY reader

The background task wasn't being properly cancelled when the
session closed, causing memory to accumulate over time.

Fixes #42
```

**Breaking change:**
```
refactor(core)!: change config from dict to pydantic model

BREAKING CHANGE: Config is now a pydantic BaseSettings class
instead of a plain dict. Update imports accordingly.

Migration:
  Before: config['BACKEND_PORT']
  After:  config.BACKEND_PORT
```

**Pro tip:** Use the `.gitmessage` template in your editor:
```bash
git config commit.template .gitmessage
```

---

## Pre-Commit Checklist

The pre-commit hook handles most of this, but here's what happens:

### 1. Common Mistakes Check

❌ **Blocks commit if found:**
- `import pdb` or `breakpoint()` (debug code)
- `print(...)` statements (use logging)
- `console.log` in JavaScript (use proper logging)

⚠️ **Warns but allows:**
- `TODO` or `FIXME` without issue number

### 2. Tests

✅ **Must pass:**
```bash
pytest
```

If tests fail, commit is blocked. No exceptions.

### 3. Type Checking

✅ **Must pass:**
```bash
mypy core/ server/ integrations/ cli/
```

Type errors block commit. Use `# type: ignore` only with a reason.

### 4. Code Formatting

🎨 **Automatically applied:**
```bash
black --line-length 100 .
isort .
```

Your code gets beautified before commit. You're welcome.

### 5. Commit Message Check

⚠️ **Warns if:**
- Not conventional commit format
- First line > 72 characters

---

## Pull Request Guidelines

### Description Template

```markdown
## What
Brief description of the change

## Why
Why is this change needed?

## How
How does it work? (architecture, key decisions)

## Testing
- [ ] Added unit tests
- [ ] Added integration tests
- [ ] Tested manually
- [ ] Updated documentation

## Screenshots
(if UI changes)

Closes #123
```

### Review Process

1. **Self-review first**
   - Read your own diff
   - Check for debug code
   - Verify tests pass
   - Update docs if needed

2. **Request review** (if team exists)
   - Tag relevant people
   - Explain any tricky parts
   - Be patient

3. **Address feedback**
   - Push new commits to same branch
   - Don't force push after review
   - Respond to comments

4. **Merge**
   - Use "Squash and merge" (keeps main clean)
   - Delete branch after merge
   - Update local main: `git checkout main && git pull`

---

## Common Scenarios

### Forgot to create branch, already committed to main

```bash
# 1. Create branch from current state
git branch feature/oops-forgot-to-branch

# 2. Reset main to origin
git checkout main
git reset --hard origin/main

# 3. Switch to your branch
git checkout feature/oops-forgot-to-branch

# 4. Push and create PR
git push -u origin feature/oops-forgot-to-branch
```

### Need to update branch with latest main

```bash
# Option 1: Merge (preserves history)
git checkout feature/your-branch
git merge main

# Option 2: Rebase (cleaner history)
git checkout feature/your-branch
git rebase main

# Resolve conflicts if any, then:
git push --force-with-lease origin feature/your-branch
```

### Accidentally committed sensitive data

```bash
# 1. Remove from last commit
git rm --cached path/to/sensitive/file
git commit --amend

# 2. Add to .gitignore
echo "path/to/sensitive/file" >> .gitignore
git add .gitignore
git commit -m "chore: add sensitive file to gitignore"

# 3. If already pushed, force push (CAREFUL!)
git push --force-with-lease origin feature/your-branch
```

**Note:** If already merged to main, you'll need to rewrite history (dangerous) or rotate the secrets.

### Want to undo last commit (not pushed)

```bash
# Keep changes, undo commit
git reset --soft HEAD~1

# Discard changes and commit (CAREFUL!)
git reset --hard HEAD~1
```

### Made too many commits, want to squash before PR

```bash
# Interactive rebase to squash last 3 commits
git rebase -i HEAD~3

# In editor, change 'pick' to 'squash' for commits to squash
# Save and exit
# Edit combined commit message
# Force push
git push --force-with-lease origin feature/your-branch
```

---

## Git Aliases (Optional but Clutch)

Add to `~/.gitconfig`:

```ini
[alias]
    # Quick status
    s = status -sb

    # Pretty log
    lg = log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit

    # Last commit
    last = log -1 HEAD --stat

    # Undo last commit (keep changes)
    undo = reset --soft HEAD~1

    # Amend last commit without editing message
    amend = commit --amend --no-edit

    # List branches by date
    branches = branch --sort=-committerdate

    # Delete merged branches
    cleanup = "!git branch --merged | grep -v '\\*\\|main\\|master' | xargs -n 1 git branch -d"
```

Usage:
```bash
git s              # Quick status
git lg             # Pretty log
git last           # Show last commit
git undo           # Undo last commit
git amend          # Amend without editing message
git cleanup        # Delete merged branches
```

---

## When Things Go Wrong

### "I messed up my branch completely"

```bash
# Nuclear option: start fresh from main
git checkout main
git pull
git checkout -b feature/fresh-start

# Cherry-pick specific commits from old branch if needed
git cherry-pick <commit-hash>
```

### "I pushed to main by accident"

1. **If no one else pulled it yet:**
   ```bash
   git reset --hard origin/main~1
   git push --force origin main
   ```

2. **If others already pulled:**
   - Create a revert commit instead
   - Or accept your fate and move on
   - Learn for next time

### "Git says I have conflicts"

```bash
# 1. See conflicted files
git status

# 2. Open each file, look for:
<<<<<<< HEAD
your changes
=======
their changes
>>>>>>> branch-name

# 3. Edit to keep what you want, remove markers

# 4. Mark as resolved
git add path/to/file

# 5. Continue merge/rebase
git merge --continue
# or
git rebase --continue
```

---

## The Golden Rules

1. **Never commit directly to main** (use branches)
2. **Never force push to main** (you'll get fired)
3. **Never commit secrets** (use .env and .gitignore)
4. **Never commit broken code** (tests must pass)
5. **Never write vague commit messages** ("fix stuff" is not acceptable)
6. **Always pull before push** (avoid conflicts)
7. **Always run tests before commit** (pre-commit hook helps)
8. **Always review your own diff** (catch mistakes early)

---

## Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Best Practices](https://dev.to/mcheremnov/git-for-entry-level-developers-a-practical-guide-2gch)
- [Atlassian Git Tutorials](https://www.atlassian.com/git/tutorials)
- [Oh Shit, Git!?!](https://ohshitgit.com/) (for when you mess up)

---

**Remember:** Git is your time machine and safety net. Use it well and it'll save your ass. Use it poorly and... well, you'll learn. 😅

**Pro tip:** The best way to learn Git is to mess up and fix it. Don't be afraid to experiment in a test branch!
