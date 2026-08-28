"""Tests for the Zone hierarchy and ZoneFactory (M1)."""

from __future__ import annotations

import pytest

from models.drone import Drone
from models.zone import BlockedZone, NormalZone, PriorityZone, ZoneFactory
from parsing.errors import ParseError


def test_normal_zone_entry_cost() -> None:
    """A normal zone costs one turn to enter."""
    assert NormalZone("a", 0, 0).entry_cost == 1


def test_restricted_zone_entry_cost() -> None:
    """A restricted zone costs two turns to enter."""
    assert ZoneFactory().build("restricted", "r", 0, 0).entry_cost == 2


def test_priority_zone_entry_cost() -> None:
    """A priority zone costs one turn to enter (but is preferred)."""
    assert isinstance(ZoneFactory().build("priority", "p", 0, 0), PriorityZone)


def test_blocked_zone_is_inaccessible() -> None:
    """A blocked zone reports itself as inaccessible."""
    zone = ZoneFactory().build("blocked", "b", 0, 0)
    assert isinstance(zone, BlockedZone)
    assert zone.is_accessible is False


def test_factory_rejects_unknown_type() -> None:
    """An unknown zone type raises a ParseError."""
    with pytest.raises(ParseError):
        ZoneFactory().build("bogus", "x", 0, 0)


def test_default_capacity_is_one() -> None:
    """A fresh zone with no occupants has capacity for one drone."""
    zone = NormalZone("a", 0, 0)
    assert zone.has_capacity() is True
    zone.occupants.append(Drone(1, zone))
    assert zone.has_capacity() is False


def test_unlimited_zone_always_has_capacity() -> None:
    """A zone built with unlimited=True always accepts more drones."""
    zone = NormalZone("hub", 0, 0, unlimited=True)
    zone.occupants.extend(Drone(i, zone) for i in range(3))
    assert zone.has_capacity() is True
