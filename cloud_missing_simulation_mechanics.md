# CLOUD DECK - MISSING SIMULATION MECHANICS ANALYSIS

## CARDS REQUIRING IMPLEMENTATION

### 1. **Sigarda's Aid**
**Oracle Text**: "You may cast Equipment spells as though they had flash. Whenever an Equipment enters the battlefield under your control, you may attach it to target creature you control."

**Missing Mechanics**:
- ❌ Flash for equipment casting
- ❌ Auto-attach equipment on ETB (free equip)
- ✓ ETB triggers exist

**Implementation Required**:
- Add "flash_equipment" property to card
- Add ETB trigger that auto-attaches equipment without paying equip cost
- Modify `equip_equipment()` to support free equip via flag

---

### 2. **Ardenn, Intrepid Archaeologist**
**Oracle Text**: "At the beginning of combat on your turn, you may attach any number of Auras and Equipment you control to target permanent or player."

**Missing Mechanics**:
- ❌ "Beginning of combat" phase/trigger
- ❌ Mass equipment movement
- ✓ Equipment attachment exists

**Implementation Required**:
- Add "beginning_of_combat" trigger event
- Create `process_beginning_of_combat_triggers()` method (already exists at line 3837!)
- Add ability to move equipment without paying equip costs
- Implement trigger for Ardenn

---

### 3. **Kemba, Kha Regent**
**Oracle Text**: "At the beginning of your upkeep, create a 2/2 white Cat creature token for each Equipment attached to Kemba, Kha Regent."

**Missing Mechanics**:
- ❌ Upkeep phase/step
- ❌ Upkeep triggers
- ❌ Token generation based on equipment count
- ✓ Token creation exists

**Implementation Required**:
- Add "upkeep" trigger event
- Create `process_upkeep_triggers()` method
- Add upkeep trigger for Kemba that counts attached equipment
- Create 2/2 cat tokens with appropriate stats

---

### 4. **Stonehewer Giant** / **Stoneforge Mystic**
**Oracle Text (Stonehewer Giant)**: "{1}{W}, {T}: Search your library for an Equipment card, put it onto the battlefield, attach it to a creature you control, then shuffle."

**Oracle Text (Stoneforge Mystic)**: "When this enters, you may search your library for an Equipment card, reveal it, put it into your hand, then shuffle. {1}{W}: You may put an Equipment card from your hand onto the battlefield."

**Missing Mechanics**:
- ❌ Tutor equipment from library
- ❌ Put equipment directly onto battlefield (bypassing mana cost)
- ✓ ETB triggers exist
- ✓ Activated abilities exist

**Implementation Required**:
- Add library search for equipment subtype
- Add "put onto battlefield" for equipment (bypassing cast)
- Add activated ability for Stoneforge

---

### 5. **Batterskull** / **Kaldra Compleat**
**Oracle Text (Batterskull)**: "Living weapon (When this Equipment enters, create a 0/0 black Phyrexian Germ creature token, then attach this to it.)"

**Oracle Text (Kaldra Compleat)**: "Living weapon. Equipped creature gets +5/+5 and has first strike, trample, indestructible, haste, and "Whenever this creature deals combat damage to a player, draw a card.""

**Missing Mechanics**:
- ❌ Living Weapon keyword
- ❌ Auto-create token on equipment ETB
- ❌ Auto-attach equipment to created token
- ✓ Token creation exists
- ✓ Equipment attachment exists

**Implementation Required**:
- Detect "living weapon" keyword in oracle text
- Create 0/0 Germ token when equipment enters battlefield
- Auto-attach equipment to the token (free equip)
- Parse multiple keywords granted by equipment

---

### 6. **Adeline, Resplendent Cathar**
**Oracle Text**: "Adeline, Resplendent Cathar's power is equal to the number of creatures you control. Whenever you attack, for each opponent, create a 1/1 white Human creature token that's tapped and attacking that opponent."

**Missing Mechanics**:
- ❌ Dynamic P/T based on creature count
- ❌ Attack trigger that creates multiple tokens
- ❌ Tokens enter tapped and attacking
- ✓ Attack triggers exist
- ✓ Token creation exists

**Implementation Required**:
- Add P/T calculation based on creature count (update each trigger)
- Parse "create X tokens for each opponent" pattern
- Implement tokens entering tapped and attacking (without declaring attackers)
- Handle multiple opponent simulation (assume 3 opponents in commander)

---

### 7. **Fireshrieker**
**Oracle Text**: "Equipped creature has double strike. Equip {2}"

**Missing Mechanics**:
- ❌ Double strike keyword
- ❌ Double strike combat damage
- ✓ Keyword granting via equipment exists (see line 167-171)

**Implementation Required**:
- Add `has_double_strike` property to creatures
- Modify combat damage calculation to deal damage twice
- Add double strike to keyword parsing in `_apply_equipped_keywords()`
- Handle interaction with first strike

---

### 8. **Aggravated Assault**
**Oracle Text**: "{3}{R}{R}: Untap all creatures you control. After this main phase, there is an additional combat phase followed by an additional main phase. Activate only as a sorcery."

**Missing Mechanics**:
- ❌ Extra combat phases
- ❌ Additional main phases
- ❌ Untap all creatures
- ✓ Activated abilities exist

**Implementation Required**:
- Add `extra_combat_phases` counter
- Create method to trigger additional combat
- Implement creature untapping
- Add "activate only as sorcery" timing restriction
- Track phase progression (main1 -> combat -> main2)

---

### 9. **Wyleth, Soul of Steel**
**Oracle Text**: "Whenever Wyleth, Soul of Steel attacks, draw a card for each Aura and Equipment attached to it."

**Missing Mechanics**:
- ❌ Count equipment attached to specific creature
- ❌ Draw cards based on equipment count on attack
- ✓ Attack triggers exist
- ✓ Draw card mechanism exists

**Implementation Required**:
- Add helper method `count_equipment_attached(creature)`
- Parse attack trigger that counts equipment
- Draw cards equal to count in attack trigger

---

### 10. **Akroma's Memorial**
**Oracle Text**: "Creatures you control have flying, first strike, vigilance, trample, haste, and protection from black and from red."

**Missing Mechanics**:
- ❌ Mass keyword granting (global effect)
- ❌ Vigilance keyword
- ❌ Trample keyword
- ❌ Protection from color
- ✓ Haste exists
- ✓ First strike exists

**Implementation Required**:
- Add global effect tracking for artifacts/enchantments
- Add keywords: `has_vigilance`, `has_trample`, `has_protection_black`, `has_protection_red`
- Modify attack/combat to respect vigilance (don't tap)
- Modify combat damage to respect trample (excess damage)
- Add `check_global_effects()` method to apply keywords to all creatures

---

## SUMMARY OF MISSING SIMULATION FEATURES

### ❌ Missing Phases/Steps:
1. **Upkeep step** - Required for Kemba, others
2. **Beginning of combat step** - Required for Ardenn (PARTIALLY EXISTS at line 3837)
3. **Extra combat phases** - Required for Aggravated Assault

### ❌ Missing Keywords:
1. **Double strike** - Required for Fireshrieker, combat damage
2. **Vigilance** - Required for Akroma's Memorial, attack without tapping
3. **Trample** - Required for Akroma's Memorial, excess damage
4. **Protection** - Required for Akroma's Memorial
5. **Living Weapon** - Required for Batterskull, Kaldra Compleat

### ❌ Missing Mechanics:
1. **Equipment cost reduction** - Sigarda's Aid (free equip)
2. **Auto-attach equipment on ETB** - Sigarda's Aid, Living Weapon
3. **Equipment moving without cost** - Ardenn
4. **Library search for equipment** - Stonehewer Giant, Stoneforge Mystic
5. **Put permanent onto battlefield (bypassing cost)** - Stoneforge Mystic
6. **Dynamic P/T** - Adeline (power = creature count)
7. **Tokens enter tapped and attacking** - Adeline
8. **Count equipment attached to creature** - Wyleth
9. **Global keyword effects** - Akroma's Memorial
10. **Extra combat tracking** - Aggravated Assault

### ✓ Already Implemented:
1. ✓ Equipment attachment (`equip_equipment()` at line 1020)
2. ✓ Equipment ETB triggers
3. ✓ Attack triggers (`_execute_triggers("attack")` at line 575)
4. ✓ Token creation (multiple implementations)
5. ✓ First strike (line 170-171)
6. ✓ Haste
7. ✓ ETB triggers
8. ✓ Activated abilities
9. ✓ Draw cards

---

## IMPLEMENTATION PRIORITY

### HIGH PRIORITY (Core Mechanics):
1. **Upkeep triggers** - Required for Kemba (upkeep token generation)
2. **Living Weapon** - Required for Batterskull, Kaldra Compleat
3. **Double strike** - Combat mechanic, affects multiple cards
4. **Equipment count tracking** - Required for Wyleth, Kemba
5. **Auto-attach equipment (free)** - Required for Sigarda's Aid, Living Weapon

### MEDIUM PRIORITY (Strategy Enhancers):
6. **Beginning of combat triggers** - Required for Ardenn (check if already exists!)
7. **Attack-based token generation** - Required for Adeline
8. **Equipment tutoring** - Required for Stonehewer Giant, Stoneforge Mystic
9. **Vigilance** - Quality of life, less critical

### LOW PRIORITY (Advanced):
10. **Extra combat phases** - Complex, affects turn structure
11. **Trample** - Combat mechanic, less critical for equipment deck
12. **Global effects** - Akroma's Memorial, complex implementation

---

## NEXT STEPS

1. ✅ Analyze what mechanics are missing
2. ⏳ Implement upkeep phase and triggers
3. ⏳ Implement Living Weapon keyword
4. ⏳ Implement double strike combat
5. ⏳ Implement equipment count tracking for Wyleth
6. ⏳ Implement auto-attach equipment for Sigarda's Aid
7. ⏳ Check if beginning_of_combat triggers exist (line 3837)
8. ⏳ Implement Adeline's attack tokens
9. ⏳ Implement equipment tutoring
10. ⏳ Test all mechanics with Cloud deck simulation

---

## CODE LOCATIONS TO MODIFY

### Primary Files:
- **`Simulation/boardstate.py`** - Main simulation engine (4800+ lines)
  - Add upkeep phase triggers
  - Add living weapon mechanic
  - Add double strike combat
  - Add vigilance, trample keywords
  - Add global effects tracking
  - Add extra combat phases

- **`Simulation/oracle_text_parser.py`** - Card parsing (762 lines)
  - Parse living weapon keyword
  - Parse double strike
  - Parse vigilance, trample
  - Parse equipment-count triggers
  - Parse global keyword effects

### Helper Modules:
- **`Simulation/mana_utils.py`** - Mana handling (if needed)
- **`shared_mechanics.py`** - Shared detection logic

### Test Files:
- **`Simulation/tests/`** - Add tests for new mechanics
- Create `test_living_weapon.py`
- Create `test_double_strike.py`
- Create `test_upkeep_triggers.py`
- Create `test_cloud_deck.py`
