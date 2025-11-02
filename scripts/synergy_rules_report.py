"""
Synergy Rules Report
Runs a curated set of two-card pairs against detect_* rules and prints a summary.

Usage:
  python -m scripts.synergy_rules_report
"""

from typing import List, Tuple, Callable, Dict, Optional
import sys

# Ensure local path
sys.path.insert(0, '/Users/lucymoreira/projetos/Deck_optimizer/Deck_synergy')

from src.synergy_engine import rules as R


Pair = Tuple[str, Callable[[Dict, Dict], Optional[Dict]], Dict, Dict]


def pairs_to_test() -> List[Pair]:
    # Cards
    scepter = {'name':'Isochron Scepter','oracle_text':'Imprint — When Isochron Scepter enters the battlefield, you may exile an instant card with mana value 2 from your hand. {2}, {T}: You may copy the exiled card.'}
    reversal = {'name':'Dramatic Reversal','type_line':'Instant','oracle_text':'Untap all nonland permanents you control.'}
    assault = {'name':'Aggravated Assault','oracle_text':'{3}{R}{R}: Untap all creatures you control. After this main phase, there is an additional combat phase followed by an additional main phase.'}
    neheb = {'name':'Neheb, the Eternal','oracle_text':'At the beginning of your postcombat main phase, add {R} for each 1 life your opponents have lost this turn.'}
    presence = {'name':"Enchantress's Presence",'type_line':'Enchantment','oracle_text':'Whenever you cast an enchantment spell, draw a card.'}
    rancor = {'name':'Rancor','type_line':'Enchantment — Aura','oracle_text':'Enchant creature. Enchanted creature gets +2/+0 and has trample. When Rancor is put into a graveyard from the battlefield, return Rancor to its owner\'s hand.'}
    yp = {'name':'Young Pyromancer','type_line':'Creature — Human Shaman','oracle_text':'Whenever you cast an instant or sorcery spell, create a 1/1 red Elemental creature token.'}
    opt = {'name':'Opt','type_line':'Instant','oracle_text':'Scry 1. Draw a card.'}
    fling = {'name':'Fling','type_line':'Instant','oracle_text':'As an additional cost to cast this spell, sacrifice a creature. Fling deals damage equal to the sacrificed creature\'s power to any target.'}
    ball = {'name':'Ball Lightning','type_line':'Creature — Elemental','oracle_text':'Trample, haste. At the beginning of the end step, sacrifice Ball Lightning.'}
    archdruid = {'name':'Elvish Archdruid','type_line':'Creature — Elf Druid','card_types':{'main_types':['Creature'],'subtypes':['Elf','Druid']},'oracle_text':'Other Elf creatures you control get +1/+1.'}
    llanowar = {'name':'Llanowar Elves','type_line':'Creature — Elf Druid','card_types':{'main_types':['Creature'],'subtypes':['Elf','Druid']},'oracle_text':'{T}: Add {G}.'}

    return [
        ("tap_untap_engines", R.detect_tap_untap_engines, scepter, reversal),
        ("extra_combat", R.detect_extra_combat_synergy, assault, neheb),
        ("enchantress_effects", R.detect_enchantress_effects, presence, rancor),
        ("spellslinger_payoffs", R.detect_spellslinger_payoffs, yp, opt),
        ("fling_effects", R.detect_fling_effects, fling, ball),
        ("tribal_synergy", R.detect_tribal_synergy, archdruid, llanowar),
    ]


def main():
    print("\nSynergy Rules Report (curated pairs)\n")
    header = f"{'Rule':28s} | {'Hit':3s} | Result"
    print(header)
    print("-" * len(header))
    for name, fn, a, b in pairs_to_test():
        try:
            res = fn(a, b)
            hit = 'YES' if res else 'NO'
            rname = (res or {}).get('name', '')
            print(f"{name:28s} | {hit:3s} | {rname}")
        except Exception as e:
            print(f"{name:28s} | ERR | {e}")


if __name__ == '__main__':
    main()

