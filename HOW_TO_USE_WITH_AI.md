# How to Work with AI Models on This Project

**Last Updated:** 2025-11-14

This guide shows you how to effectively use AI coding assistants (like Claude, ChatGPT, Copilot, etc.) to improve and maintain your MTG Deck Analyzer project.

---

## 🎯 Quick Start: Best Practices

### 1. Always Start with Context
When opening a new AI conversation, provide this initial context:

```
I have an MTG deck analyzer project built with Python, Dash, and Flask.
Please read AI_GUIDE.md to understand the project structure.

[Then ask your specific question]
```

### 2. Be Specific with File References
Instead of vague questions, reference specific files:

**❌ Bad:** "Why isn't synergy detection working?"

**✅ Good:** "The synergy between [[Ashnod's Altar]] and [[Skullclamp]] isn't being detected.
Can you check src/synergy_engine/rules.py and src/utils/aristocrats_extractor.py
to see if we're missing the sacrifice outlet pattern?"

### 3. Provide Examples
Always include example cards or scenarios:

**❌ Bad:** "Add prowess support"

**✅ Good:** "Add prowess mechanic detection. Example cards:
- [[Monastery Swiftspear]] - 'Prowess (Whenever you cast...'
- [[Soul-Scar Mage]] - 'Prowess'
- [[Stormchaser Mage]] - 'Flying, haste, prowess'

See src/utils/keyword_extractor.py for pattern, then add synergy rules
for prowess + spell-based strategies."

---

## 📋 Common Tasks & How to Ask

### Task 1: Understanding the Codebase

**Goal:** Learn how something works

**Good Prompts:**
```
"Explain how the synergy detection system works. Start with
src/synergy_engine/analyzer.py and show me the flow from
loading a deck to displaying synergies on the graph."
```

```
"I want to understand how the simulation calculates deck power.
Walk me through:
1. Simulation/simulate_game.py - the main loop
2. Simulation/boardstate.py - how damage is tracked
3. src/simulation/metrics.py - how the final score is calculated"
```

```
"Show me all the places where [[Doubling Season]] would be processed:
1. Where it's loaded from the database
2. How its abilities are parsed
3. What synergy rules detect it
4. How it appears in the graph"
```

**Tips:**
- Ask for step-by-step walkthroughs
- Request file-by-file explanations
- Ask AI to trace a single card through the entire system

---

### Task 2: Adding New Features

**Goal:** Implement new functionality

**Good Prompts:**

#### Adding New Synergy Detection
```
"I want to add detection for the 'Flash' mechanic. Here's what I need:

1. Create src/utils/flash_extractor.py to detect:
   - Cards with 'Flash' keyword
   - Cards that give other cards flash ('You may cast...')
   - Example: [[Teferi, Mage of Zhalfir]], [[Vedalken Orrery]]

2. Add synergy rules in src/synergy_engine/rules.py for:
   - Flash creatures + cards that care about instants
   - Flash + end-of-turn triggers
   - Flash + opponent's turn matters

3. Add 'flash' category to src/synergy_engine/categories.py

4. Write tests in tests/test_flash_extractors.py

Show me the implementation for each step."
```

#### Adding Dashboard Features
```
"I want to add a 'Deck Statistics' panel to the dashboard showing:
- Total synergy score
- Average synergy per card
- Top 5 most synergistic cards
- Weakest cards (bottom 5)

1. Where should I add this in app.py?
2. What callbacks do I need?
3. Show me the Dash layout code
4. How do I calculate these metrics from the synergy graph?"
```

#### Adding Simulation Mechanics
```
"Add support for 'Prowess' triggers to the simulation. Here's what I need:

1. Update Simulation/oracle_text_parser.py to detect:
   - 'Prowess' keyword
   - 'Prowess N' (N is a number)
   - Pattern: r'prowess\s*(\d*)'

2. Update Simulation/boardstate.py to:
   - Track prowess triggers when noncreature spells are cast
   - Apply temporary +1/+1 until end of turn
   - Handle multiple prowess instances

3. Add test in Simulation/tests/test_prowess.py with:
   - [[Monastery Swiftspear]] (prowess)
   - [[Monastery Mentor]] (prowess + creates tokens)

Show me the complete implementation."
```

**Tips:**
- Break down features into numbered steps
- Reference similar existing features as examples
- Be specific about what files to modify
- Always ask for tests

---

### Task 3: Fixing Bugs

**Goal:** Debug and fix issues

**Good Prompts:**
```
"I'm getting this error when loading a deck with [[The Gitrog Monster]]:

[Paste error message here]

The card has text: 'At the beginning of your upkeep, sacrifice The Gitrog Monster
unless you sacrifice a land. You may play an additional land on each of your turns.
Whenever one or more land cards are put into your graveyard from anywhere, draw a card.'

Can you:
1. Check src/utils/graveyard_extractor.py for the land trigger pattern
2. Check Simulation/oracle_text_parser.py for parsing this ability
3. Identify which part is failing
4. Provide a fix with test case"
```

```
"The synergy graph is showing duplicate edges between [[Pitiless Plunderer]]
and [[Mayhem Devil]]. They should only have one edge with strength 5.

Check:
1. src/synergy_engine/rules.py - check_synergy() function
2. src/utils/graph_builder.py - how edges are created
3. app.py - cytoscape element creation

Find where duplicates are being added and fix it."
```

**Tips:**
- Include full error messages
- Provide the specific cards causing issues
- Show what you expected vs. what actually happened
- Ask AI to check multiple potential sources of the bug

---

### Task 4: Improving Performance

**Goal:** Make the app faster

**Good Prompts:**
```
"The synergy analysis is taking 45 seconds for a 100-card deck. Profile the performance:

1. Identify slow functions in src/synergy_engine/analyzer.py
2. Check if we're doing redundant card lookups
3. See if regex_cache is being used properly
4. Suggest optimizations (caching, parallelization, algorithm improvements)

Show me specific code changes with before/after comparisons."
```

```
"The graph rendering freezes the browser with 500+ synergy edges. Options:

1. Add edge filtering (only show strength >= 3)
2. Implement pagination or virtualization
3. Use a different layout algorithm
4. Add a 'simplified view' mode

Which approach is best? Show me how to implement it in app.py."
```

**Tips:**
- Describe the performance problem (time, memory, UI freeze)
- Ask for multiple solution options
- Request before/after comparisons
- Ask about trade-offs

---

### Task 5: Testing

**Goal:** Write or fix tests

**Good Prompts:**
```
"Write comprehensive tests for src/utils/token_extractor.py. Cover:

1. Simple token creation ('Create a 1/1 white Soldier')
2. Token creation with abilities ('Create a 2/2 black Zombie with decayed')
3. Token doublers ('If an effect would create tokens, it creates twice that many')
4. Edge cases (X tokens, token copies, multiple types)

Show me the complete test file with at least 10 test cases."
```

```
"All tests in tests/test_damage_extractors.py are failing after my changes
to src/utils/damage_extractor.py. Here's my change:

[Paste your code change]

Why are the tests failing? Fix either the tests or my code."
```

**Tips:**
- Reference existing test files as templates
- Ask for multiple test cases covering edge cases
- Request both positive and negative test cases
- Ask for test documentation

---

## 🎨 Feature Ideas & How to Ask

### Complete Feature Requests

#### Idea: Add Deck Comparison
```
"I want to compare two decks side-by-side. Design and implement:

1. UI: Add a 'Compare Decks' button and modal in app.py
2. Backend: Create src/utils/deck_comparison.py with:
   - compare_synergies(deck1, deck2) -> shows overlap & differences
   - compare_power(deck1, deck2) -> simulation comparison
   - recommend_swaps(deck1, deck2) -> suggest card swaps
3. Visualization: Side-by-side graphs showing shared vs. unique synergies
4. Tests: tests/test_deck_comparison.py

Show me the implementation plan first, then we'll build it step by step."
```

#### Idea: Add Meta Analysis
```
"Add a feature to analyze deck against the current EDH meta:

1. Data: Create data/meta/top_cards.json with most-played cards by color
2. Analysis: src/synergy_engine/meta_analyzer.py to:
   - Compare deck's card choices vs. meta staples
   - Identify budget alternatives to expensive cards
   - Suggest meta-relevant cards that synergize with the deck
3. UI: Add 'Meta Analysis' tab to dashboard
4. Update: Script to fetch latest meta data from EDHRec

What's the best approach? Show me a detailed implementation plan."
```

#### Idea: Export to TTS/MTGO
```
"Add deck export functionality:

1. Support formats:
   - Tabletop Simulator (.json)
   - MTGO (.dek)
   - Arena (.txt)
   - Cockatrice (.cod)

2. Implementation:
   - src/utils/deck_exporters.py with format converters
   - Add 'Export' dropdown in dashboard
   - Generate downloadable files

3. Features:
   - Include commander indicator
   - Validate deck legality before export
   - Add deck statistics as comments

Show me how to implement this."
```

---

## 🔍 Debugging Techniques with AI

### Technique 1: Trace Execution
```
"Trace the execution flow when I click 'Load Deck' with this Archidekt URL:
[URL]

Show me:
1. Which callback in app.py handles the click
2. How it calls src/api/archidekt.py
3. How cards are loaded from src/api/local_cards.py
4. How synergy analysis is triggered
5. How the graph is built and displayed

Include line numbers and key function names."
```

### Technique 2: Compare Working vs. Broken
```
"This synergy works: [[Ashnod's Altar]] + [[Skullclamp]]
This synergy doesn't: [[Phyrexian Altar]] + [[Skullclamp]]

Both are sacrifice outlets. Compare:
1. How each card is tagged in src/utils/aristocrats_extractor.py
2. What patterns are matched in src/synergy_engine/rules.py
3. Why one is detected and the other isn't

Show me the difference and fix it."
```

### Technique 3: Reproduce Minimal Example
```
"Create a minimal test case that reproduces this issue:

Problem: Graph doesn't render when deck has no commander

Minimal deck:
- 10 basic lands
- No commander specified

Expected: Graph shows 10 nodes
Actual: Blank screen, console error [paste error]

Create a test in tests/test_graph_rendering.py that reproduces this,
then fix the bug in src/utils/graph_builder.py."
```

---

## 💡 Advanced AI Assistance

### Code Review Requests
```
"Review my implementation of prowess detection:

[Paste your code]

Check for:
1. Correctness - does it match MTG rules?
2. Performance - any inefficient patterns?
3. Style - consistent with existing code?
4. Edge cases - what am I missing?
5. Tests - do I need more test coverage?

Provide specific suggestions with code examples."
```

### Refactoring Requests
```
"The src/synergy_engine/rules.py file is 2000+ lines and hard to maintain.

Refactor it into:
1. rules/combat_rules.py
2. rules/graveyard_rules.py
3. rules/ramp_rules.py
4. rules/token_rules.py
5. rules/equipment_rules.py

Show me:
1. How to split the file
2. How to maintain backward compatibility
3. How to update imports across the codebase
4. How to update tests

Provide step-by-step migration plan."
```

### Architecture Questions
```
"I want to add machine learning-based synergy detection using card embeddings.

Current: Rule-based detection in src/synergy_engine/rules.py
Proposed: Hybrid rule-based + ML

Questions:
1. Where should the ML model live? (new src/ml/ directory?)
2. How should it integrate with existing analyzer.py?
3. Should it run in parallel with rules or as a fallback?
4. How do I train it? What data do I need?
5. How do I prevent it from slowing down the analysis?

Provide architectural guidance and implementation approach."
```

---

## 🚨 Common Mistakes to Avoid

### ❌ Mistake 1: Too Vague
```
"Make the synergy detection better"
```
**Problem:** AI doesn't know what "better" means or where to start

**✅ Fix:**
```
"The aristocrats synergy detection misses cards like [[Pitiless Plunderer]]
that create treasures on death. Add detection for:
1. 'create a Treasure token' on death
2. Update src/utils/aristocrats_extractor.py
3. Add test cases in tests/test_aristocrats_extractor.py"
```

### ❌ Mistake 2: No Context
```
"This is broken, fix it"
```
**Problem:** AI doesn't know what's broken, where, or what the expected behavior is

**✅ Fix:**
```
"The simulation isn't counting damage from [[Purphoros, God of the Forge]].

Card text: 'Whenever another creature enters under your control,
Purphoros deals 2 damage to each opponent.'

Expected: 2 damage per creature ETB
Actual: 0 damage counted

Files to check:
- Simulation/oracle_text_parser.py (ETB trigger parsing)
- Simulation/boardstate.py (ETB trigger execution)
- Simulation/tests/test_etb_triggers.py (existing tests)

Show me the bug and fix."
```

### ❌ Mistake 3: Asking for Everything at Once
```
"Rewrite the entire codebase to be faster, add 50 new features,
fix all bugs, and deploy it"
```
**Problem:** Too broad, impossible to complete, will produce low-quality results

**✅ Fix:**
```
"Let's improve performance in phases:

Phase 1 (this conversation): Profile synergy analysis and identify bottlenecks
Phase 2 (next): Implement caching improvements
Phase 3 (later): Parallelize card processing

For Phase 1, run performance analysis on src/synergy_engine/analyzer.py
with a 100-card deck. Show me where the time is spent."
```

### ❌ Mistake 4: No Verification Step
```
"Add this feature [describes feature]"
[AI provides code]
[You copy-paste without understanding]
[Everything breaks]
```

**✅ Fix:**
```
"Add this feature [describes feature]

Before implementation:
1. Explain the approach
2. Show me which files you'll modify
3. List potential side effects
4. Recommend how to test it

Then show me the code with explanations."
```

---

## 📚 Learning Resources to Share with AI

When working with AI on complex MTG mechanics, provide these resources:

### MTG Rules Reference
```
"I'm implementing [mechanic]. Here are the official rules:

[Paste relevant rules from MTG Comprehensive Rules]

Now implement detection for this in [specific file]."
```

### Example Cards
```
"Here are 5 example cards with [mechanic]:

1. [[Card Name 1]] - [Oracle text]
2. [[Card Name 2]] - [Oracle text]
3. [[Card Name 3]] - [Oracle text]
4. [[Card Name 4]] - [Oracle text]
5. [[Card Name 5]] - [Oracle text]

Extract common patterns and implement detection."
```

### Existing Code Patterns
```
"Follow the same pattern as [existing feature]:

1. Look at src/utils/token_extractor.py for extraction pattern
2. Look at src/synergy_engine/rules.py lines 500-600 for synergy rules
3. Look at tests/test_token_extractors.py for test pattern

Apply this pattern to implement [new feature]."
```

---

## 🎯 Success Checklist

Before considering a task complete, verify:

- [ ] Code follows existing patterns and style
- [ ] Tests are written and passing
- [ ] Documentation is updated (docstrings, README, etc.)
- [ ] No regressions (existing tests still pass)
- [ ] Performance is acceptable (no major slowdowns)
- [ ] Edge cases are handled
- [ ] Error handling is proper
- [ ] Code is commented where complex

**Good Follow-up Prompt:**
```
"Review this implementation against the project's success checklist:
[Paste checklist above]

Identify what's missing and provide improvements."
```

---

## 🤝 Working Iteratively with AI

### Best Practice: Small Iterations

**❌ Bad Approach:**
```
Session 1: "Build entire deck comparison feature"
[Gets overwhelmed, incomplete code]
```

**✅ Good Approach:**
```
Session 1: "Design the deck comparison feature architecture"
Session 2: "Implement the backend comparison logic"
Session 3: "Add the UI components"
Session 4: "Write tests and fix bugs"
Session 5: "Optimize performance and polish"
```

### Maintaining Context Across Sessions

**At the start of each new session:**
```
"I'm working on [feature name] for my MTG deck analyzer.

Previous progress:
- Session 1: Designed architecture (see docs/deck_comparison_design.md)
- Session 2: Implemented backend (src/utils/deck_comparison.py)

Current session goal: Add UI components to app.py

Please review the existing code before we continue."
```

### Saving Progress

**At the end of each session:**
```
"Summarize what we accomplished this session:
1. Files created/modified
2. Features implemented
3. Tests added
4. What's left to do

Format it as a markdown summary I can reference next time."
```

---

## 🎓 Example: Complete Feature Development

Let's walk through a complete feature development conversation:

### Session 1: Planning
```
User: "I want to add a 'Deck Power Rating' feature that shows a 1-10 score
based on simulation results. Where should this go and how should it work?"

AI: [Provides architectural guidance]

User: "That makes sense. Create a detailed implementation plan with:
1. File structure
2. Function signatures
3. Algorithm approach
4. Integration points
5. Testing strategy"

AI: [Provides detailed plan]

User: "Looks good! Let's start with step 1 in the next session.
Save this plan to docs/power_rating_implementation.md"
```

### Session 2: Backend Implementation
```
User: "I'm implementing the Deck Power Rating feature.
See docs/power_rating_implementation.md for the plan.

Today: Implement the backend calculation in src/simulation/power_rating.py

Requirements:
- calculate_power_rating(simulation_results) -> float (1-10)
- Consider: win rate, avg damage, turn efficiency, consistency
- Include confidence intervals

Show me the implementation with docstrings."

AI: [Provides code]

User: "This looks good. Now write tests in tests/test_power_rating.py.
Include: edge cases, known examples, validation tests."

AI: [Provides tests]

User: "Run the tests and verify they pass. Fix any issues."
```

### Session 3: UI Integration
```
User: "Continuing the Deck Power Rating feature.

Completed:
- Backend: src/simulation/power_rating.py ✓
- Tests: tests/test_power_rating.py ✓ (all passing)

Today: Add UI to dashboard (app.py)

Show me:
1. Where to add the power rating display (which section?)
2. Callback to calculate and update it
3. Styling to make it prominent
4. Integration with existing simulation results"

AI: [Provides UI code]

User: "Test this locally and show me what it looks like.
Any visual improvements?"

AI: [Provides improvements]
```

### Session 4: Polish & Documentation
```
User: "Final touches on Deck Power Rating feature.

Add:
1. Tooltip explaining how the rating is calculated
2. Breakdown showing contribution of each factor
3. Comparison to 'average EDH deck'
4. User documentation in docs/USER_GUIDE.md

Then do a final code review and ensure everything is production-ready."

AI: [Provides final touches]

User: "Perfect! Create a summary of this feature for RELEASE_NOTES.md"
```

---

## 🚀 Quick Reference: Common Prompts

### Understanding Code
- "Explain how [feature] works, starting with [file]"
- "Trace the execution of [action] through the codebase"
- "Show me all files related to [topic]"

### Adding Features
- "I want to add [feature]. Show me: (1) architecture, (2) implementation plan, (3) integration points"
- "Implement [specific function] in [file] with tests"
- "Add UI for [feature] following the pattern in [existing feature]"

### Fixing Bugs
- "This error occurs: [error]. Check [files] and fix it"
- "Why isn't [expected behavior] working? Debug [file]"
- "Compare why [case A] works but [case B] doesn't"

### Improving Code
- "Refactor [file] to be more [quality: readable/efficient/maintainable]"
- "Review my code for [issues: bugs/performance/style]"
- "Optimize [slow operation] in [file]"

### Testing
- "Write tests for [file] covering [scenarios]"
- "Why is [test] failing? Fix it"
- "Add edge case tests for [feature]"

---

## 📞 Getting Help

If you're stuck working with AI on this project:

1. **Check the AI_GUIDE.md** - Comprehensive technical reference
2. **Review existing code** - Find similar features as examples
3. **Start simple** - Begin with a minimal example, then expand
4. **Ask for explanations** - Don't just copy code, understand it
5. **Iterate** - Small steps, test frequently

---

**Happy coding with AI! This project is designed to be AI-friendly.** 🤖✨

---

*Last updated: 2025-11-14*
*For technical reference, see: [AI_GUIDE.md](AI_GUIDE.md)*
*For project overview, see: [README.md](README.md)*
