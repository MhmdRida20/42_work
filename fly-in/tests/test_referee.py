"""Referee: replays the printed turns and checks every rule on its own.

The Referee uses nothing from the simulator, so a bug there can't hide
here: it only gets the map from the parser and the lines main.py
printed. Capacity follows the conservative reading (plan section 1): a
flying drone already counts in the zone it flies to, and a link counts
every drone that moves on it, landing drones included.
"""

from __future__ import annotations

from collections import Counter

import pytest

from main import main
from models.connection import Connection
from models.network import Network
from models.zone import Zone
from parsing.parser import Parser


class Referee:
    """Replay one run's printed lines and collect every broken rule."""

    def __init__(self, network: Network, nb_drones: int) -> None:
        """Put every drone in the start zone.

        Args:
            network: The parsed map.
            nb_drones: How many drones the run must deliver.
        """
        self.network = network
        self.at: dict[int, Zone] = {
            drone: network.start for drone in range(1, nb_drones + 1)
        }
        # Drone id -> (connection, destination, turns still to fly).
        self.flying: dict[int, tuple[Connection, Zone, int]] = {}
        self.errors: list[str] = []

    def check(self, lines: list[str]) -> list[str]:
        """Replay every turn and return the broken rules.

        Args:
            lines: The run's output, one line per turn.

        Returns:
            One message per broken rule; empty if the run is valid.
        """
        for turn, line in enumerate(lines, start=1):
            self._play(turn, line)
        end = self.network.end
        lost = [d for d, zone in self.at.items() if zone is not end]
        lost += list(self.flying)
        if lost:
            self.errors.append(f"not delivered: {sorted(lost)}")
        return self.errors

    def _fail(self, turn: int, message: str) -> None:
        """Record one broken rule."""
        self.errors.append(f"turn {turn}: {message}")

    def _play(self, turn: int, line: str) -> None:
        """Apply one turn's moves, then check both capacities."""
        used: Counter[Connection] = Counter()
        moved: set[int] = set()
        for token in line.split():
            label, _, target = token.partition("-")
            drone = int(label[1:]) if label[1:].isdigit() else 0
            known = drone in self.at or drone in self.flying
            if not label.startswith("D") or not known or drone in moved:
                self._fail(turn, f"bad or repeated token {token}")
                continue
            moved.add(drone)
            if drone in self.flying:
                self._fly(turn, drone, target, used)
            else:
                self._leave(turn, drone, target, used)
        for drone in self.flying:
            if drone not in moved:
                self._fail(turn, f"D{drone} waited on a connection")
        self._check_capacity(turn, used)

    def _leave(
        self, turn: int, drone: int, target: str, used: Counter[Connection]
    ) -> None:
        """Move a drone out of its zone: a plain move or a take-off."""
        here = self.at[drone]
        if here is self.network.end:
            self._fail(turn, f"D{drone} moved after delivery")
            return
        link = self._find_link(here, target)
        if link is None:
            self._fail(
                turn, f"D{drone}-{target} is not a link from {here.name}"
            )
            return
        dest = link.other_end(here)
        if not dest.is_accessible:
            self._fail(turn, f"D{drone} entered blocked {dest.name}")
            return
        takes_off = target == link.name
        if takes_off != (dest.entry_cost > 1):
            self._fail(
                turn,
                f"D{drone}-{target}: entering {dest.name} takes "
                f"{dest.entry_cost} turn(s)",
            )
        used[link] += 1
        del self.at[drone]
        if takes_off:
            self.flying[drone] = (link, dest, dest.entry_cost - 1)
        else:
            self.at[drone] = dest

    def _fly(
        self, turn: int, drone: int, target: str, used: Counter[Connection]
    ) -> None:
        """Move a flying drone along its link; it lands on the last turn."""
        link, dest, turns_left = self.flying[drone]
        turns_left -= 1
        expected = dest.name if turns_left == 0 else link.name
        if target != expected:
            self._fail(
                turn, f"D{drone}-{target}: expected D{drone}-{expected}"
            )
        used[link] += 1
        if turns_left == 0:
            del self.flying[drone]
            self.at[drone] = dest
        else:
            self.flying[drone] = (link, dest, turns_left)

    def _find_link(self, here: Zone, target: str) -> Connection | None:
        """Return the link from ``here`` that ``target`` names, if any.

        ``target`` is the zone at the other end, or the link's own name
        exactly as the map wrote it.
        """
        for link in self.network.neighbors(here):
            if target in (link.other_end(here).name, link.name):
                return link
        return None

    def _check_capacity(self, turn: int, used: Counter[Connection]) -> None:
        """Fail every zone or link holding more drones than it allows."""
        held = Counter(self.at.values())
        held.update(dest for _, dest, _ in self.flying.values())
        for zone, count in held.items():
            if not zone.unlimited and count > zone.max_drones:
                self._fail(
                    turn,
                    f"{zone.name} holds {count} drones, max {zone.max_drones}",
                )
        for link, count in used.items():
            if count > link.max_link_capacity:
                self._fail(
                    turn,
                    f"{link.name} used by {count} drones, "
                    f"max {link.max_link_capacity}",
                )


@pytest.mark.parametrize(
    ("map_path", "turns"),
    [
        ("maps/example.map", 6),
        ("maps/easy_linear.map", 6),
        ("maps/easy/01_linear_path.txt", 4),
        ("maps/easy/02_simple_fork.txt", 4),
        ("maps/easy/03_basic_capacity.txt", 4),
        ("maps/medium/01_dead_end_trap.txt", 8),
        ("maps/medium/02_circular_loop.txt", 15),
        ("maps/medium/03_priority_puzzle.txt", 7),
        ("maps/hard/01_maze_nightmare.txt", 13),
        ("maps/hard/02_capacity_hell.txt", 16),
        ("maps/hard/03_ultimate_challenge.txt", 26),
        ("maps/challenger/01_the_impossible_dream.txt", 43),
        ("maps/edge_start_to_end.map", 3),
        ("maps/edge_restricted_end.map", 5),
        ("maps/edge_two_restricted.map", 7),
        ("maps/edge_priority_tie.map", 2),
        ("maps/edge_crowded_tie.map", 15),
        ("maps/edge_1000_drones.map", 501),
    ],
)
def test_every_map_breaks_no_rule(
    map_path: str, turns: int, capsys: pytest.CaptureFixture[str]
) -> None:
    """main.py's output on each map is valid and keeps its turn count."""
    assert main(["main.py", map_path]) == 0
    lines = capsys.readouterr().out.splitlines()
    network, nb_drones = Parser().parse_file(map_path)

    assert Referee(network, nb_drones).check(lines) == []
    assert len(lines) == turns


SMALL_MAP = """\
nb_drones: 2
start_hub: s 0 0
hub: a 1 0 [max_drones=2]
hub: b 1 1
hub: r 2 0 [zone=restricted max_drones=2]
hub: q 2 1 [zone=restricted]
hub: x 1 2 [zone=blocked]
end_hub: e 3 0
connection: s-a
connection: s-b [max_link_capacity=2]
connection: s-r
connection: s-q [max_link_capacity=2]
connection: s-x
connection: a-e
connection: b-e
connection: r-e
connection: q-e
""".splitlines()


def test_referee_accepts_a_valid_run() -> None:
    """A legal hand-made run on the small map has no broken rule."""
    network, nb_drones = Parser().parse_lines(SMALL_MAP)
    lines = ["D1-a D2-s-r", "D1-e D2-r", "D2-e"]

    assert Referee(network, nb_drones).check(lines) == []


@pytest.mark.parametrize(
    ("lines", "broken"),
    [
        (["D1-e"], "not a link from s"),
        (["D1-r-s"], "D1-r-s is not a link from s"),
        (["D1-x"], "entered blocked x"),
        (["D1-b D2-b"], "b holds 2"),
        (["D1-s-q D2-s-q"], "q holds 2"),
        (["D1-a D2-a"], "s-a used by 2"),
        (["D1-s-r", "D1-r D2-s-r"], "s-r used by 2"),
        (["D1-r"], "entering r takes 2"),
        (["D1-s-a"], "entering a takes 1"),
        (["D1-s-r", "D1-s-r"], "expected D1-r"),
        (["D1-s-r", "D2-a"], "D1 waited on a connection"),
        (["D1-a D1-a"], "repeated token D1-a"),
        (["D3-a"], "repeated token D3-a"),
        (["D1-a", "D1-e", "D1-a"], "moved after delivery"),
        (["D1-a", "D1-e"], "not delivered: [2]"),
    ],
)
def test_referee_catches_each_broken_rule(
    lines: list[str], broken: str
) -> None:
    """Each hand-made bad run is reported with the rule it breaks."""
    network, nb_drones = Parser().parse_lines(SMALL_MAP)
    errors = Referee(network, nb_drones).check(lines)

    assert any(broken in error for error in errors), errors
