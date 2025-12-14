class Creature:
    def __init__(self, name, power, toughness, mana_cost=None):
        """        Initializes a Creature object.
        Args:
            name (str): Name of the creature.
            power (int): Power of the creature.
            toughness (int): Toughness of the creature.
            mana_cost (str): Mana cost to cast the creature. Defaults to None.
        """
        self.name = name
        self.power = power
        self.toughness = toughness
        self.mana_cost = None

    def take_damage(self, damage):
        """Mark damage on this creature and return the damage dealt.

        Note: In this simplified simulation, damage doesn't modify toughness.
        The combat system manually checks if creatures should die.
        """
        # Return the full damage amount without modifying toughness
        return damage

    def is_alive(self):
        return self.toughness > 0

    def __str__(self):
        return f"{self.name} (Power: {self.power}, Toughness: {self.toughness})"
