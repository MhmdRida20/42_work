import functools
import operator
from collections.abc import Callable
from typing import Any


def spell_reducer(spells: list[int], operation: str) -> int:
    if not spells:
        return 0

    operations: dict[str, Callable[[int, int], int]] = {
        "add": operator.add,
        "multiply": operator.mul,
        "max": lambda left, right: left if left >= right else right,
        "min": lambda left, right: left if left <= right else right,
    }

    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")

    return functools.reduce(operations[operation], spells)


def partial_enchanter(base_enchantment: Callable[[int, str, str], str],
                      ) -> dict[str, Callable[[str], str]]:
    return {
        "fire": functools.partial(base_enchantment, 50, "fire"),
        "ice": functools.partial(base_enchantment, 50, "ice"),
        "lightning": functools.partial(
            base_enchantment,
            50,
            "lightning",
        ),
    }


@functools.lru_cache(maxsize=None)
def memoized_fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n < 2:
        return n
    return memoized_fibonacci(n - 1) + memoized_fibonacci(n - 2)


def spell_dispatcher() -> Callable[[Any], str]:

    @functools.singledispatch
    def dispatch(spell: Any) -> str:
        del spell
        return "Unknown spell type"

    @dispatch.register(int)
    def handle_damage(spell: int) -> str:
        return f"Damage spell: {spell} damage"

    @dispatch.register(str)
    def handle_enchantment(spell: str) -> str:
        return f"Enchantment: {spell}"

    @dispatch.register(list)
    def handle_multi_cast(spell: list) -> str:
        return f"Multi-cast: {len(spell)} spells"
    return dispatch


def main():
    powers = [10, 20, 30, 40]

    print("Testing spell reducer...")
    print(f"Sum: {spell_reducer(powers, 'add')}")
    print(f"Product: {spell_reducer(powers, 'multiply')}")
    print(f"Max: {spell_reducer(powers, 'max')}")

    print("\nTesting partial enchanter...")

    def base_enchantment(power: int, element: str, target: str) -> str:
        return f"{element.capitalize()} enchant on {target} ({power} power)"
    variants = partial_enchanter(base_enchantment)
    for name, fn in variants.items():
        print(name, "->", fn("Sword"))

    print("\nTesting memoized fibonacci...")
    print(f"Fib(0): {memoized_fibonacci(0)}")
    print(f"Fib(1): {memoized_fibonacci(1)}")
    print(f"Fib(10): {memoized_fibonacci(10)}")
    print(f"Fib(15): {memoized_fibonacci(15)}")

    print("\nTesting spell dispatcher...")
    dispatcher = spell_dispatcher()
    print(dispatcher(42))
    print(dispatcher("fireball"))
    print(dispatcher([1, 2, 3]))


if __name__ == "__main__":
    main()
