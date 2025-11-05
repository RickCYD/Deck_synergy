# Contributing to MTG Commander Deck Synergy Visualizer

Thank you for your interest in contributing! This document provides guidelines and best practices for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Contribution Guidelines](#contribution-guidelines)
- [Review Process](#review-process)

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior
- Be respectful and constructive in all interactions
- Welcome newcomers and help them get started
- Focus on what is best for the community and project
- Show empathy towards other community members

### Unacceptable Behavior
- Harassment, discrimination, or offensive comments
- Trolling, insulting comments, or personal attacks
- Publishing others' private information
- Any conduct that could reasonably be considered inappropriate

## How to Contribute

### Reporting Bugs

**Before submitting a bug report:**
1. Check existing [Issues](https://github.com/username/Deck_synergy/issues) to avoid duplicates
2. Test with the latest version from `main` branch
3. Gather reproduction steps and examples

**When submitting a bug report, include:**
- Clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Deck URL or card names if applicable
- Screenshots if relevant
- Your environment (OS, Python version, browser)

**Example:**
```markdown
### Bug: Recruiter of the Guard shows synergy with Peregrine Drake

**Steps to Reproduce:**
1. Load deck with Recruiter of the Guard and Peregrine Drake
2. Click on Recruiter of the Guard
3. Observe synergy listed

**Expected:** No synergy (Peregrine Drake has toughness 3, Recruiter only finds toughness ≤2)

**Actual:** Synergy shown in graph

**Environment:** macOS 13, Python 3.9, Chrome 120
```

### Suggesting Enhancements

**Enhancement proposals should include:**
- Clear use case and motivation
- Detailed description of the proposed feature
- Examples of how it would work
- Potential implementation approach (if known)

**Example:**
```markdown
### Feature: Detect Storm Synergies

**Use Case:** Storm decks are a popular archetype but currently not well detected

**Proposal:** Add storm synergy detection for:
- Cards with storm mechanic
- Cost reducers (Baral, Goblin Electromancer)
- Copy effects (Fork, Twincast)

**Implementation:**
- Add `storm` and `cost_reducer` tags to preprocessed cards
- Add complementary pair: storm + cost_reducer
- Create storm_synergies.py module

**Examples:**
- Grapeshot + Baral, Chief of Compliance
- Tendrils of Agony + Cost reducers
```

### Contributing Code

**Types of contributions we welcome:**
- Bug fixes
- New synergy detection
- Performance improvements
- Documentation improvements
- Test coverage
- UI/UX enhancements

**Not currently accepting:**
- Major architectural changes (please discuss first)
- Support for other formats besides Commander
- Alternative data sources (we use Scryfall/Archidekt)

## Development Workflow

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/Deck_synergy.git
cd Deck_synergy
git remote add upstream https://github.com/original/Deck_synergy.git
```

### 2. Create a Branch

```bash
# Branch naming convention:
# feature/description   - New features
# fix/description       - Bug fixes
# docs/description      - Documentation
# refactor/description  - Code refactoring

git checkout -b feature/storm-synergies
```

### 3. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download card data
python3 scripts/create_minimal_cards.py
```

### 4. Make Changes

```bash
# Make your changes
# Add tests if applicable
# Update documentation

# Test your changes
python app.py
# Load a deck and verify your changes work
```

### 5. Commit Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: Add storm synergy detection

- Add storm and cost_reducer tags
- Create storm_synergies.py module
- Add complementary pair for storm + cost_reducer
- Update documentation with storm examples"
```

**Commit Message Format:**
```
<type>: <short summary>

<optional detailed description>

<optional footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 6. Push and Create PR

```bash
# Push to your fork
git push origin feature/storm-synergies

# Create Pull Request on GitHub
# Fill out the PR template
```

### 7. Address Review Feedback

```bash
# Make requested changes
git add .
git commit -m "fix: Address review feedback"
git push origin feature/storm-synergies
```

## Contribution Guidelines

### Code Style

**Python Style:**
- Follow PEP 8 guidelines
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable names

**Formatting:**
```bash
# Optional: Use black for auto-formatting
pip install black
black src/ app.py
```

**Example:**
```python
# Good
def detect_storm_synergies(card1: Dict, card2: Dict) -> List[Dict]:
    """
    Detect synergies between storm cards and enablers.

    Storm decks benefit from cost reducers and copy effects
    that increase storm count.
    """
    synergies = []

    card1_text = card1.get('oracle_text', '').lower()
    card2_text = card2.get('oracle_text', '').lower()

    if 'storm' in card1_text and 'cost less' in card2_text:
        synergies.append({
            'category': 'Storm Enabler',
            'description': f"{card2['name']} reduces storm costs",
            'strength': 2.0
        })

    return synergies

# Bad
def dss(c1,c2):
    s=[]
    if 'storm' in c1['oracle_text'].lower() and 'cost less' in c2['oracle_text'].lower():
        s.append({'category':'Storm Enabler','description':f"{c2['name']} reduces storm costs",'strength':2.0})
    return s
```

### Documentation

**All new functions must include:**
- Docstring with description
- Args and Returns documentation
- Examples if complex

```python
def my_function(param1: str, param2: int) -> Dict:
    """
    Brief one-line description.

    Longer description providing context, usage notes,
    and any important considerations.

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Dictionary containing:
        - key1: Description
        - key2: Description

    Examples:
        >>> my_function('test', 5)
        {'result': 'value'}
    """
    pass
```

### Testing

**Manual Testing Requirements:**
1. Test with at least 3 different decks
2. Verify synergies appear correctly in graph
3. Check synergy descriptions are accurate
4. Ensure no performance degradation

**Testing Checklist:**
```markdown
- [ ] Loaded deck with new synergy
- [ ] Synergy appears in graph
- [ ] Synergy description is accurate
- [ ] No console errors
- [ ] Performance acceptable (<30s for 100 card deck)
- [ ] Works with edge cases (0 synergies, many synergies)
```

### Pull Request Guidelines

**PR Title Format:**
```
<type>: <concise description>

Examples:
feat: Add storm synergy detection
fix: Correct Recruiter of the Guard toughness restriction
docs: Update README with installation steps
```

**PR Description Must Include:**
1. **What**: Description of changes
2. **Why**: Motivation and context
3. **How**: Implementation approach
4. **Testing**: How you tested the changes
5. **Screenshots**: If UI changes

**PR Template:**
```markdown
## Description
Brief description of what this PR does.

## Motivation
Why is this change needed? What problem does it solve?

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Tested with [deck name/URL]
- [ ] Verified synergy detection works correctly
- [ ] No console errors
- [ ] Performance acceptable

## Screenshots (if applicable)
[Add screenshots here]

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Tested manually with multiple decks
- [ ] No breaking changes
```

### Review Process

**What to Expect:**
1. **Initial Review**: Within 1-3 days
2. **Feedback**: Constructive suggestions for improvements
3. **Iterations**: May require 1-2 rounds of changes
4. **Approval**: At least one maintainer approval required
5. **Merge**: Maintainer will merge approved PRs

**Review Criteria:**
- Code quality and readability
- Follows contribution guidelines
- Includes appropriate documentation
- Tested and working
- No breaking changes without discussion

## Types of Contributions

### Easy: Documentation Improvements
**Good first contribution!**
- Fix typos or unclear explanations
- Add examples to existing docs
- Improve code comments
- Update README with FAQ

### Medium: Bug Fixes
**Requires familiarity with codebase**
- Fix incorrect synergy detection
- Correct scoring calculations
- UI/UX improvements
- Performance optimizations

### Advanced: New Features
**Requires deep understanding of system**
- New synergy categories
- New card roles
- Architectural improvements
- Major refactoring

## Getting Help

**Before asking for help:**
1. Read the [Development Guide](DEVELOPMENT.md)
2. Check existing Issues and PRs
3. Review [Architecture Documentation](ARCHITECTURE.md)

**Where to ask:**
- **General questions**: [GitHub Discussions](https://github.com/username/Deck_synergy/discussions)
- **Bug reports**: [GitHub Issues](https://github.com/username/Deck_synergy/issues)
- **PR questions**: Comment on your PR

**When asking for help, include:**
- What you're trying to accomplish
- What you've tried so far
- Relevant code snippets or error messages
- Links to specific files or lines if applicable

## Recognition

Contributors will be:
- Listed in project README
- Credited in release notes
- Thanked in commit messages

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the MTG Commander community! 🎉
