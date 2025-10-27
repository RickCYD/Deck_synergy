Mana Simulation: Calculations and How To Use The Graphs
=======================================================

What the simulation does
- Simulates many games (Monte Carlo) from opening hand to a chosen max turn.
- Each turn: draw, play one land, optionally cast accelerants (rocks/ramp), then evaluate whether colors and spells are available.
- Lands that enter tapped are unavailable the turn they enter (if enabled).
- Multi‑color sources are flexible but provide one mana per turn.

Key outputs and definitions
- All Colors Available (probability): chance you can produce each color in your deck’s identity at least once by that turn.
- At Least One Spell Castable (probability): chance there is at least one non‑accelerant spell in hand that you can pay for that turn.
- Available Mana Percentiles: p10/p50/p90 show distribution of total usable sources that turn, after accelerants.
- Opening Hand Lands Histogram: probability for each land count in opening 7.
- Lands in Hand CDF (focus turn): cumulative probability distribution of how many lands remain in hand by the chosen turn (after plays and ramp each turn).
- Color Limitation Rate (per color): fraction of in‑hand non‑accelerant spells that are uncastable and would become castable with +1 source of that color.
- Playable Fraction: fraction of in‑hand non‑accelerant spells that are castable that turn.

How to read the main chart
- Top panel
  - Left axis: probabilities for All Colors Available and At Least One Spell Castable.
  - Right axis: available mana percentiles (p10–p90 band, p50 line). Use this to see the “mana curve” progression.
- Bottom panel
  - Dotted lines (W/U/B/R/G): color‑specific bottlenecks — higher means that color is blocking more spells in hand.
  - % Cards Playable: how saturated the hand is overall with castable options.

Color saturation/missing status (summary above chart)
- For the focus turn (configurable by the “Per‑card turn” control):
  - saturated: P(color available) > 0.90 and color limitation rate < 0.05
  - missing: P(color available) < 0.60 or color limitation rate > 0.15
  - balanced: otherwise
  - Suggestion: if color is not saturated, we estimate +K sources likely helps.

How suggestions are calculated
- For each uncastable spell in hand, we compute the minimal number of extra sources (k = 1..3) of a given color needed to make that specific spell castable, holding other factors constant.
- Aggregated across simulations and hands, we build a per‑color histogram of k.
- We then choose the smallest k where at least 80% of color‑limited cases would be solved. This becomes the “suggest +K sources” recommendation per color for the focus turn.
- Interpretation:
  - If the suggestion is +1, many spells are blocked only by one pip in that color.
  - If +2 or +3, your deck often lacks depth in that color (multiple pips or simultaneous color demands).

How to improve your deck using the graphs
- If “All Colors Available” lags early while bottom‑panel dotted lines are high for a color C, add more C sources (basics, duals, signets/talismans) until the limitation rate falls and the line chart rises.
- If Available Mana p50 stalls (flat median) while “% Cards Playable” is low, consider more total lands or accelerants.
- If one color’s limitation rate is high and the suggestion says “+2 U sources,” prioritize adding at least two blue sources (or more flexible duals that include U).
- Cross‑check with per‑card table (probability castable by turn T) to see which key spells are lagging and whether fixing their colors helps your game plan.

Assumptions and scope
- Hybrid/phyrexian costs are approximated (ignored special semantics); X is treated as 0.
- Rocks are modeled as +1 flexible source from the next turn onward.
- Ramp/fetch heuristics add a tapped land and one to hand; specific fetching logic is simplified.
- Complex untap conditions are not fully modeled.

Tips
- Increase iterations for smoother curves (e.g., 100k+).
- Use “Per‑card turn” to align the summary and per‑card table with a key turn for your deck (e.g., T4 for midrange).
