# Contributing to Claude on the Go

Thank you for your interest in contributing to Claude on the Go! This project aims to provide private, local-first mobile access to Claude Code CLI. We welcome contributions of all kinds - code, documentation, bug reports, and feature requests.

## Quick Start

Get up and running in 3 steps:

```bash
# 1. Clone and install
git clone https://github.com/yourusername/claude-on-the-go.git
cd claude-on-the-go
pip install -e .

# 2. Set up environment
export CLAUDE_CODE_PATH=/usr/local/bin/claude

# 3. Start the server
claude-on-the-go start
```

## Development Setup

### Clone and Install

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/claude-on-the-go.git
cd claude-on-the-go

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests with pytest
pytest

# Run with coverage report
pytest --cov=core --cov=server --cov=integrations

# Run specific test file
pytest tests/test_pty_manager.py
```

### Type Checking

```bash
# Run mypy for type checking
mypy core/ server/ integrations/

# Check specific module
mypy core/pty_manager.py
```

### Code Formatting

```bash
# Format code with black (line length 100)
black --line-length 100 .

# Sort imports with isort
isort .

# Run both together
black --line-length 100 . && isort .
```

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

Key directories:
- `core/` - PTY manager, session storage, mDNS discovery
- `server/` - FastAPI WebSocket streaming, REST endpoints
- `client/` - PWA for mobile access
- `integrations/` - Push notifications, Tailscale, QR codes
- `legacy/` - Original open source implementation
- `tests/` - Unit and integration tests

## Making Changes

**⚠️ IMPORTANT: Never commit directly to `main` branch!**

We follow a feature branch workflow with pull requests. See [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md) for detailed guide.

### Workflow

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Branch** from `main` with a descriptive name (e.g., `feature/add-rest-api`)
4. **Code** your changes following our style guide
5. **Test** your changes thoroughly (pre-commit hook runs automatically)
6. **Commit** with conventional commit messages
7. **Push** to your fork
8. **PR** back to the main repository
9. **Merge** after review (squash merge preferred)

### Branch Naming

Use descriptive branch names with prefixes:

- `feature/add-tailscale-integration` - New features
- `fix/websocket-reconnection-bug` - Bug fixes
- `docs/update-contributing-guide` - Documentation updates
- `refactor/simplify-pty-manager` - Code refactoring

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]

[optional footer]
```

Types:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: Add mDNS service discovery for local network

fix: Resolve WebSocket reconnection timeout issue

docs: Update installation instructions for Windows
```

## Code Style

### Python

- **Black** for code formatting (line length 100)
- **isort** for import sorting
- **mypy** for static type checking
- **Type hints required** for all function signatures
- **Docstrings required** in Google style for public APIs
- **Tests required** for new features and bug fixes

### Type Hints Example

```python
from typing import Optional, Dict, Any

async def create_session(
    user_id: str,
    config: Optional[Dict[str, Any]] = None
) -> Session:
    """Create a new terminal session.

    Args:
        user_id: Unique identifier for the user
        config: Optional session configuration

    Returns:
        A new Session instance

    Raises:
        ValueError: If user_id is empty
    """
    pass
```

### Docstring Style

Use Google-style docstrings:

```python
def parse_terminal_theme(config_path: str) -> TerminalTheme:
    """Parse terminal configuration and extract theme.

    Args:
        config_path: Path to terminal configuration file

    Returns:
        TerminalTheme object with extracted colors and fonts

    Raises:
        FileNotFoundError: If config file doesn't exist
        ParseError: If config format is invalid
    """
    pass
```

## Terminal Parser Contributions (Community Welcome!)

We welcome community contributions for terminal theme parsers! Currently we have:

- ✅ **Ghostty** - Fully implemented
- ⏳ **iTerm2, Alacritty, Kitty, Warp, Hyper, Terminal.app, Windows Terminal** - Contributions welcome!

### Why We Need Your Help

This is a **bootstrapped solo project** built by a developer supporting his family. I can't pay for contributions yet, but I want to be transparent about where we are:

**Current status:**
- Building toward first revenue (mobile app launch)
- Every feature brings us closer to sustainability
- When profitable, I'll revisit contributor rewards

**What you get:**
- Your name in CONTRIBUTORS.md and release notes
- Credit as original author for your terminal
- First-class support for your terminal of choice
- Satisfaction of helping a bootstrapped open-source project

### Available Parsers (7 total)

1. **iTerm2** (macOS) - `~/Library/Preferences/com.googlecode.iterm2.plist` (Most requested!)
2. **Alacritty** (Cross-platform) - `~/.config/alacritty/alacritty.yml`
3. **Kitty** (Cross-platform) - `~/.config/kitty/kitty.conf`
4. **Warp** (macOS) - `~/.warp/themes/`
5. **Hyper** (Cross-platform) - `~/.hyper.js`
6. **Terminal.app** (macOS) - `~/Library/Preferences/com.apple.Terminal.plist`
7. **Windows Terminal** (Windows) - `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_*\`

### Requirements

To contribute a parser, your PR should include:

1. **Full theme extraction**:
   - All 18 ANSI colors (8 normal + 8 bright)
   - Foreground, background, and cursor colors
   - Font family and size
   - Graceful handling of missing config (return default theme)

2. **Comprehensive tests**:
   - Unit tests with 80%+ coverage
   - Example config file in `tests/fixtures/`
   - Test cases for missing/malformed configs

3. **Documentation**:
   - Add parser to `docs/ADDING_TERMINALS.md`
   - Include example config snippet
   - Document any terminal-specific quirks

4. **Code quality**:
   - Passes all CI checks
   - Follows code style guidelines
   - Type hints and docstrings

### How to Contribute

1. Create an issue announcing which parser you're working on
2. Implement the parser following `docs/ADDING_TERMINALS.md`
3. Submit a PR referencing the issue
4. Get credit in CONTRIBUTORS.md and release notes!

See `docs/ADDING_TERMINALS.md` for detailed implementation guide.

## Pull Request Process

### Before Submitting

1. **Create an issue first** for significant changes
   - Discuss your approach
   - Get feedback from maintainers
   - Avoid duplicate work

2. **Ensure your code**:
   - Passes all tests: `pytest`
   - Passes type checking: `mypy core/ server/ integrations/`
   - Is properly formatted: `black --check .` and `isort --check .`
   - Has no linting errors: `flake8`

3. **Write good commit messages**:
   - Use conventional commit format
   - Be descriptive but concise
   - Reference issue numbers

### Submitting

1. Push your branch to your fork
2. Open a PR against the `main` branch
3. Fill out the PR template completely
4. Link to related issues using keywords (fixes #123, closes #456)
5. Add screenshots/videos for UI changes

### Review Process

1. **Automated checks**: CI must pass (tests, type checking, formatting)
2. **Code review**: At least 1 approving review required
3. **Discussion**: Address reviewer feedback promptly
4. **Merge**: Maintainers will squash merge when approved

### After Merge

- Your contribution will be credited in release notes
- Bounties will be paid within 7 days
- You'll be added to contributors list

## Community Guidelines

We are committed to providing a welcoming and inclusive environment.

### Expected Behavior

- Be respectful and considerate
- Use welcoming and inclusive language
- Accept constructive feedback gracefully
- Focus on what's best for the community
- Help newcomers get started

### Unacceptable Behavior

- Harassment, discrimination, or derogatory comments
- Trolling, insulting, or personal attacks
- Publishing others' private information
- Other conduct inappropriate in a professional setting

### Reporting

If you experience or witness unacceptable behavior, please report it to the project maintainers privately.

## Security Issues

**Do not report security vulnerabilities through public GitHub issues.**

Instead, please report them privately:
- Email: [security contact - add your email]
- GitHub Security Advisory: Use "Report a vulnerability" button

We'll respond within 48 hours and work with you to resolve the issue.

## Questions?

- **GitHub Discussions**: Ask questions, share ideas, get help
- **GitHub Issues**: Report bugs, request features
- **Documentation**: Check README.md, ARCHITECTURE.md, and docs/

Thank you for contributing to Claude on the Go!
