"""Smoke tests: verify the skeleton imports and wires together.

These do not test behavior yet (the logic is unimplemented); they
just guard against import errors and obvious signature drift. Replace
and extend them as you implement each stage.
"""

from __future__ import annotations

from models.network import Network
from models.zone import NormalZone
from parsing.parser import Parser


def test_network_starts_empty() -> None:
    """A fresh network has no zones registered."""
    assert Network().zones == {}


def test_normal_zone_entry_cost() -> None:
    """A normal zone costs one turn to enter."""
    assert NormalZone("a", 0, 0).entry_cost == 1


def test_parser_constructs() -> None:
    """The parser can be instantiated with its zone factory."""
    assert Parser().factory is not None
