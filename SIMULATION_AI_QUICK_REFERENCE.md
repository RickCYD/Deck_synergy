# 🤖 Simulation AI - Quick Reference

## Core Concept
**Goldfish Mode**: AI plays solitaire, all creatures attack unblocked, measures damage output over 10 turns.

---

## Main Phase Priority (What Order Cards Are Played)

```
1. Mana Rocks       → Play ALL rocks (accelerate mana)
2. Commander        → Cast ASAP, auto-equip all equipment
3. Ramp Spells      → Cultivate, Kodama's Reach, etc.
4. Best Creature    → Using AI scoring (see below)
5. More Creatures   → Graveyard recursion (Muldrotha, Gravecrawler)
6. Equipment        → Attach to best target (commander > legendary > high power)
7. Optimize Mana    → Use leftover mana for abilities/instants
```

---

## Creature Selection Scoring

**Higher score = cast first**

| Creature Type | Score | Example |
|---------------|-------|---------|
| Commander | +1000 | Zurgo Helmsmasher |
| Legendary (3+ power) | +500-600 | Aurelia, the Warleader |
| Mana dork | +400 | Llanowar Elves |
| Attack draw trigger | +300 | Esper Sentinel |
| Attack token trigger | +250 | Adeline, Resplendent Cathar |
| ETB draw | +200 | Mulldrifter |
| ETB tutor | +180 | Recruiter of the Guard |
| High power | +5 per power | 6/6 Dragon = +30 |
| 1/1 weenie | -50 | Penalty for weakness |

**Example**: Llanowar Elves (455) > Esper Sentinel (355) > Solemn (310)

---

## Equipment Targeting Priority

**Who gets the Sword of Fire and Ice?**

```
1. Commander (+1000)           → Zurgo Helmsmasher
2. Legendary (+500)            → Aurelia, the Warleader
3. Attack draw trigger (+300)  → Esper Sentinel
4. Double strike (+100)        → Mirran Crusader
5. Attack trigger (+150)       → Boros Reckoner
6. High power (power × 2)      → Bigger creatures
```

---

## Combat (Goldfish Mode)

```python
for creature in board:
    if creature.has_haste or turns_on_board >= 1:
        damage += creature.power
        trigger_attack_abilities(creature)
```

**All creatures attack, no blockers, all damage goes through.**

---

## Key Design Choices

| Choice | Reason |
|--------|--------|
| Play all rocks immediately | Maximize mana acceleration |
| Commander priority | Voltron/commander-centric strategies |
| Mana dorks score high | Early ramp is critical |
| Equipment on commander | Voltron strategy optimization |
| Goldfish mode | Measure deck's power ceiling |

---

## What The AI Does NOT Do

❌ Block
❌ Hold mana for removal/counterspells
❌ Make political decisions
❌ Respond to opponent threats
❌ Plan around board wipes

**Why?** It's measuring your deck's **best-case scenario power**.

---

## Metrics Tracked

- **Combat Damage**: Creature attacks
- **Drain Damage**: Blood Artist, Zulaport Cutthroat
- **Spell Damage**: Burn spells, cast triggers
- **Board Power**: Total creature power
- **Mana Efficiency**: Spent vs. unspent mana
- **Commander Cast Turn**: How fast commander comes out

---

## Reading Results

**High damage (50-70+ over 10 turns)**: Aggressive, fast deck
**Medium damage (30-50)**: Balanced, value-oriented
**Low damage (0-30)**: Slow/combo deck or mana issues

**Commander avg turn 3-4**: Good mana curve
**Commander avg turn 6+**: Too slow or mana problems

---

## Code Locations

- **AI logic**: `Simulation/boardstate.py:2650-2938`
- **Main phase**: `Simulation/simulate_game.py:457-636`
- **Combat**: `Simulation/simulate_game.py:740-768`

---

*For detailed explanation, see SIMULATION_AI_LOGIC_EXPLAINED.md*
