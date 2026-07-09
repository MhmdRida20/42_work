from collections.abc import Callable


def spell_combiner(spell1: Callable[[str, int], str],
                   spell2: Callable[[str, int], str],
                   ) -> Callable[[str, int], tuple[str, str]]:

    def combined_spell(target: str, power: int) -> tuple[str, str]:
        return spell1(target, power), spell2(target, power)

    return combined_spell


def power_amplifier(base_spell: Callable[[str, int], str],
                    multiplier: int,
                    ) -> Callable[[str, int], str]:

    def amplified_spell(target: str, power: int) -> str:
        return base_spell(target, power * multiplier)

    return amplified_spell


def conditional_caster(condition: Callable[[str, int], bool],
                       spell: Callable[[str, int], str],
                       ) -> Callable[[str, int], str]:

    def conditional_spell(target: str, power: int) -> str:
        if condition(target, power):
            return spell(target, power)
        return "Spell fizzled"

    return conditional_spell


def spell_sequence(spells: list[Callable[[str, int], str]],
                   ) -> Callable[[str, int], list[str]]:

    def sequence(target: str, power: int) -> list[str]:
        return [spell(target, power) for spell in spells]

    return sequence


def main():
    def fireball(target: str, power: int) -> str:
        return f"Fireball hits {target} for {power} damage"

    def heal(target: str, power: int) -> str:
        return f"Heals {target} for {power} HP"

    target = "Dragon"
    power = 10

    print("Testing spell combiner...")
    combined = spell_combiner(fireball, heal)
    print("Combined spell result:", combined(target, power))

    print("\nTesting power amplifier...")
    amplified = power_amplifier(fireball, 3)
    print(f"Original: {power}, Amplified call: {amplified(target, power)}")

    print("\nTesting conditional caster...")
    def condition(t, p): return p >= 5
    conditional = conditional_caster(condition, fireball)
    print(conditional(target, power))

    print("\nTesting spell sequence...")
    sequence = spell_sequence([fireball, heal])
    print(sequence(target, power))


if __name__ == "__main__":
    main()
