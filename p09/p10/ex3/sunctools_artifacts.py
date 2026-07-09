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


def partial_enchanter(
    base_enchantment: Callable[[int, str, str], str],
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
