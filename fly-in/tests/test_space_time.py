"""Tests for the space-time planner: ReservationTable and SpaceTimeFinder."""

from __future__ import annotations

from collections import Counter

import pytest

from main import main
from models.network import Network
from models.zone import Zone
from parsing.errors import NoPathError
from parsing.parser import Parser
from pathfinding.space_time import ReservationTable, SpaceTimeFinder
from simulation.scheduler import Scheduler
from simulation.simulator import Simulator


def _network(lines: list[str]) -> Network:
    """Parse a small map given as text lines."""
    network, _ = Parser().parse_lines(lines)
    return network


def _names(route: list[Zone]) -> list[str]:
    """Return the zone names of a route, for readable asserts."""
    return [zone.name for zone in route]


def _route_turns(route: list[Zone]) -> int:
    """Return how many turns a planned route takes."""
    turns = 0
    for here, there in zip(route, route[1:]):
        turns += 1 if here is there else there.entry_cost
    return turns


LINE_WITH_RESTRICTED = [
    "nb_drones: 2",
    "start_hub: s 0 0",
    "hub: r 1 0 [zone=restricted]",
    "end_hub: e 2 0",
    "connection: s-r",
    "connection: r-e",
]


def test_zone_is_free_counts_up_to_max_drones() -> None:
    """A zone is full once max_drones routes hold it; start never is."""
    network = _network(
        [
            "nb_drones: 2",
            "start_hub: s 0 0",
            "hub: a 1 0 [max_drones=2]",
            "end_hub: e 2 0",
            "connection: s-a [max_link_capacity=2]",
            "connection: a-e [max_link_capacity=2]",
        ]
    )
    s, a, e = (network.zones[name] for name in ("s", "a", "e"))
    table = ReservationTable()

    table.book_route(network, [s, a, e])
    assert table.zone_is_free(a, 1)
    table.book_route(network, [s, a, e])
    assert not table.zone_is_free(a, 1)
    assert table.zone_is_free(a, 2)
    assert table.zone_is_free(s, 1)


def test_can_move_checks_every_turn_of_a_restricted_move() -> None:
    """r is held while D1 flies in (turns 1-2); D2 may leave on turn 3."""
    network = _network(LINE_WITH_RESTRICTED)
    s, r, e = (network.zones[name] for name in ("s", "r", "e"))
    link = network.connection_between(s, r)
    table = ReservationTable()

    table.book_route(network, [s, r, e])

    assert not table.can_move(link, r, 1)
    assert not table.can_move(link, r, 2)
    assert table.can_move(link, r, 3)


def test_can_move_needs_the_zone_on_every_turn_of_the_flight() -> None:
    """r is free on turn 1 but taken on turn 2, so D2 can't take off."""
    network = _network(
        [
            "nb_drones: 2",
            "start_hub: s 0 0",
            "hub: x 1 1",
            "hub: r 1 0 [zone=restricted]",
            "end_hub: e 2 0",
            "connection: s-x",
            "connection: x-r",
            "connection: s-r",
            "connection: r-e",
        ]
    )
    s, x, r, e = (network.zones[name] for name in ("s", "x", "r", "e"))
    link = network.connection_between(s, r)
    table = ReservationTable()

    table.book_route(network, [s, x, r, e])  # D1 flies x -> r, turns 2-3

    assert not table.can_move(link, r, 1)
    assert table.can_move(link, r, 4)


def test_book_route_holds_the_zone_while_waiting() -> None:
    """A repeated zone books that zone for the waiting turn."""
    network = _network(LINE_WITH_RESTRICTED)
    s, r, e = (network.zones[name] for name in ("s", "r", "e"))
    table = ReservationTable()

    table.book_route(network, [s, r, r, e])

    assert not table.zone_is_free(r, 3)
    assert table.zone_is_free(r, 4)


def test_opposite_directions_share_the_link_capacity() -> None:
    """A link of capacity 1 carries one drone per turn, either way."""
    network = _network(
        [
            "nb_drones: 2",
            "start_hub: s 0 0",
            "hub: a 1 0",
            "hub: b 2 0",
            "end_hub: e 3 0",
            "connection: s-a",
            "connection: a-b",
            "connection: b-e",
        ]
    )
    s, a, b, e = (network.zones[name] for name in ("s", "a", "b", "e"))
    link = network.connection_between(a, b)
    table = ReservationTable()

    table.book_route(network, [s, a, b, e])  # a -> b on turn 2

    assert not table.can_move(link, a, 2)  # b -> a on the same turn
    assert table.can_move(link, a, 3)


def test_waiting_needs_room_and_costs_no_effort() -> None:
    """D1 holds a on turn 1, so nobody may wait there on that turn."""
    network = _network(
        [
            "nb_drones: 2",
            "start_hub: s 0 0",
            "hub: a 1 0",
            "end_hub: e 2 0",
            "connection: s-a",
            "connection: a-e",
        ]
    )
    s, a, e = (network.zones[name] for name in ("s", "a", "e"))
    distances = SpaceTimeFinder._distances_to_end(network)
    table = ReservationTable()
    table.book_route(network, [s, a, e])  # a on turn 1, e on turn 2

    from_turn_0 = SpaceTimeFinder._moves(network, table, distances, a, 0)
    from_turn_1 = SpaceTimeFinder._moves(network, table, distances, a, 1)

    assert (a, 1, 0) not in from_turn_0
    assert (e, 1, 2) in from_turn_0
    assert (a, 2, 0) in from_turn_1


def test_fewest_turns_beats_fewest_connections() -> None:
    """Two restricted zones (5 turns) lose to three normal ones (4)."""
    network = _network(
        [
            "nb_drones: 1",
            "start_hub: s 0 0",
            "hub: r1 1 0 [zone=restricted]",
            "hub: r2 2 0 [zone=restricted]",
            "hub: a 1 1",
            "hub: b 2 1",
            "hub: c 3 1",
            "end_hub: e 4 0",
            "connection: s-r1",
            "connection: r1-r2",
            "connection: r2-e",
            "connection: s-a",
            "connection: a-b",
            "connection: b-c",
            "connection: c-e",
        ]
    )
    [route] = SpaceTimeFinder(1).find_paths(network)
    assert _names(route) == ["s", "a", "b", "c", "e"]


def test_priority_route_wins_a_tie() -> None:
    """With equal arrival, the priority zone beats a normal one."""
    network, nb_drones = Parser().parse_file("maps/edge_priority_tie.map")
    [route] = SpaceTimeFinder(nb_drones).find_paths(network)
    assert _names(route) == ["s", "p", "e"]


def test_drones_wait_instead_of_colliding() -> None:
    """On a one-drone link, later drones wait in the start zone."""
    network, nb_drones = Parser().parse_file("maps/edge_start_to_end.map")
    routes = SpaceTimeFinder(nb_drones).find_paths(network)
    assert [_names(route) for route in routes] == [
        ["s", "e"],
        ["s", "s", "e"],
        ["s", "s", "s", "e"],
    ]


def test_example_map_uses_both_routes() -> None:
    """example.map: the drones split over both routes, in 6 turns."""
    network, nb_drones = Parser().parse_file("maps/example.map")
    routes = SpaceTimeFinder(nb_drones).find_paths(network)
    first_steps = {
        next(zone.name for zone in route if zone is not network.start)
        for route in routes
    }
    assert first_steps == {"roof1", "corridorA"}

    drones = Scheduler().assign(network, routes, nb_drones)
    assert len(Simulator(network, drones).run()) == 6


def test_second_pass_beats_an_unlucky_tie() -> None:
    """One pass takes 25 turns on this map; the second pass gets 15."""
    network, nb_drones = Parser().parse_file("maps/edge_crowded_tie.map")
    finder = SpaceTimeFinder(nb_drones)
    distances = finder._distances_to_end(network)

    _, first_pass_turns = finder._plan_all(network, distances, Counter())
    routes = finder.find_paths(network)
    drones = Scheduler().assign(network, routes, nb_drones)

    assert first_pass_turns == 25
    assert len(Simulator(network, drones).run()) == 15


def test_distances_count_turns_and_skip_blocked_zones() -> None:
    """hub reaches goal in 3 turns via corridorA; obstacleX is left out."""
    network, _ = Parser().parse_file("maps/example.map")
    distances = SpaceTimeFinder(1)._distances_to_end(network)

    assert distances["goal"] == 0
    assert distances["roof1"] == 2
    assert distances["hub"] == 3
    assert "obstacleX" not in distances


def test_distances_count_a_restricted_zone_as_two_turns() -> None:
    """s -> r1 -> r2 -> e is 3 connections but 2 + 2 + 1 = 5 turns."""
    network, _ = Parser().parse_file("maps/edge_two_restricted.map")
    distances = SpaceTimeFinder(1)._distances_to_end(network)
    assert distances == {"e": 0, "r2": 1, "r1": 3, "s": 5}


@pytest.mark.parametrize(
    "map_path",
    [
        "maps/example.map",
        "maps/easy/01_linear_path.txt",
        "maps/easy/02_simple_fork.txt",
        "maps/easy/03_basic_capacity.txt",
        "maps/medium/01_dead_end_trap.txt",
        "maps/medium/02_circular_loop.txt",
        "maps/medium/03_priority_puzzle.txt",
        "maps/hard/01_maze_nightmare.txt",
        "maps/hard/02_capacity_hell.txt",
        "maps/hard/03_ultimate_challenge.txt",
        "maps/challenger/01_the_impossible_dream.txt",
        "maps/edge_restricted_end.map",
        "maps/edge_two_restricted.map",
        "maps/edge_crowded_tie.map",
        "maps/edge_1000_drones.map",
    ],
)
def test_every_drone_arrives_when_planned(map_path: str) -> None:
    """The simulator never has to block a planned move.

    If the planner booked something the simulator then refuses, the
    drone is delayed, which the turn count alone can miss.
    """
    network, nb_drones = Parser().parse_file(map_path)
    routes = SpaceTimeFinder(nb_drones).find_paths(network)
    promised = [_route_turns(route) for route in routes]

    drones = Scheduler().assign(network, routes, nb_drones)
    lines = Simulator(network, drones).run()
    arrived: dict[int, int] = {}
    for turn, line in enumerate(lines, start=1):
        for token in line.split():
            label, _, target = token.partition("-")
            if target == network.end.name:
                arrived[int(label[1:])] = turn

    assert [arrived[d] for d in range(1, nb_drones + 1)] == promised


def test_same_plan_on_every_run() -> None:
    """Planning twice gives the same routes: nothing depends on luck."""
    network, nb_drones = Parser().parse_file(
        "maps/hard/03_ultimate_challenge.txt"
    )
    first = SpaceTimeFinder(nb_drones).find_paths(network)
    second = SpaceTimeFinder(nb_drones).find_paths(network)
    assert [_names(route) for route in first] == [
        _names(route) for route in second
    ]


@pytest.mark.parametrize(
    "map_path",
    ["maps/edge_no_path_disconnected.map", "maps/edge_no_path_blocked.map"],
)
def test_unreachable_end_raises(map_path: str) -> None:
    """No route to the end is a NoPathError, before planning starts."""
    network, nb_drones = Parser().parse_file(map_path)
    with pytest.raises(NoPathError, match="no path from 's' to 'e'"):
        SpaceTimeFinder(nb_drones).find_paths(network)


def test_unreachable_end_stops_main_cleanly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """main.py prints one error line and exits with 1, no traceback."""
    assert main(["main.py", "maps/edge_no_path_blocked.map"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: no path from 's' to 'e'\n"
