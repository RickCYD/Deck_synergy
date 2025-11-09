from dataclasses import dataclass, field
from typing import List, Callable, Any


@dataclass
class ManaAbility:
    """Representation of an activated ability that produces mana.

    The ability may have a mana ``cost`` that needs to be paid, may require
    the permanent to ``tap`` and can optionally only be usable when the
    source is equipped to a creature.  ``produces_colors`` lists the colours
    of mana the ability will generate when activated.  The constructor accepts
    lowercase colour identifiers and performs some normalisation so tests can
    rely on a consistent representation.
    """

    cost: str = ""
    produces_colors: List[str] = field(default_factory=list)
    tap: bool = False
    requires_equipped: bool = False

    def __post_init__(self):  # pragma: no cover - simple normalisation
        # normalise cost to string and colours to upper-case
        self.cost = str(self.cost or "")
        self.produces_colors = [c.upper() for c in self.produces_colors]


# ``ActivatedAbility`` previously modelled mana abilities.  Keep it as a
# backwards compatible alias so existing code importing ``ActivatedAbility``
# continues to work while new code can use the clearer ``ManaAbility`` name.
ActivatedAbility = ManaAbility


@dataclass
class TriggeredAbility:
    """Simple representation of a triggered ability.

    ``event`` describes when the ability should fire.  Supported values
    currently include ``"etb"`` for enters-the-battlefield triggers,
    ``"equip"`` for equipment being attached, ``"attack"`` for when a
    creature attacks, and ``"landfall"`` for whenever a land enters the
    battlefield under your control.
    """

    event: str
    effect: Callable[["BoardState"], Any]
    description: str = ""
    requires_haste: bool = False
    requires_flash: bool = False
    requires_another_legendary: bool = False


def sonic_attack_effect(card):
    """Return an effect that adds a +1/+1 counter to *card* when it attacks."""

    def effect(board_state):
        card.add_counter("+1/+1")

    return effect


def remove_plus_one_counter_effect(card):
    """Return an effect that removes a +1/+1 counter from *card*."""

    def effect(board_state):
        card.remove_counter("+1/+1")

    return effect


def proliferate_effect():
    """Return an effect that proliferates counters on the board."""

    def effect(board_state):
        board_state.proliferate()

    return effect
