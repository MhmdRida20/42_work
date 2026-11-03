"""Space-time planner: route each drone through (zone, turn) states.

Drones are planned one at a time, in id order. Each one searches for
its earliest arrival around what earlier drones already booked in a
reservation table, then books its own route. Waiting is just another
move in the search, so planned drones never collide and can't
deadlock.

The whole plan is made twice: the second pass avoids the zones the
first pass crowded whenever that costs no time, and the better plan
wins.
"""

from __future__ import annotations

import heapq
from collections import Counter

from models.connection import Connection
from models.network import Network
from models.zone import PriorityZone, Zone
from parsing.errors import NoPathError
from pathfinding.pathfinder import PathFinder

# A search state: a drone sitting in a zone at the end of a turn.
State = tuple[str, int]
# The parent of the first state, so every state has one.
NO_PARENT: State = ("", -1)


class ReservationTable:
    """Record how many drones use each zone and connection per turn.

    The rules match the simulator's: a drone flying into a zone holds
    its place there from take-off, it uses the connection on every
    turn of the movement, and a drone leaving a zone frees it that
    same turn.
    """

    def __init__(self) -> None:
        """Create an empty table."""
        self.zones: Counter[tuple[str, int]] = Counter()
        self.links: Counter[tuple[str, int]] = Counter()

    def zone_is_free(self, zone: Zone, turn: int) -> bool:
        """Return True if ``zone`` can hold one more drone on ``turn``."""
        if zone.unlimited:
            return True
        return self.zones[zone.name, turn] < zone.max_drones

    def can_move(self, link: Connection, zone: Zone, turn: int) -> bool:
        """Return True if a drone may start moving into ``zone``.

        Args:
            link: The connection used.
            zone: The destination zone.
            turn: The turn the movement starts on.

        Returns:
            True if the link and the zone stay available for every
            turn the movement lasts.
        """
        for used_turn in range(turn, turn + zone.entry_cost):
            if self.links[link.name, used_turn] >= link.max_link_capacity:
                return False
            if not self.zone_is_free(zone, used_turn):
                return False
        return True

    def book_route(self, network: Network, route: list[Zone]) -> None:
        """Book every step of a planned route.

        Args:
            network: The network the route belongs to.
            route: Zones in order, from turn 0; a repeated zone is a
                one-turn wait.
        """
        turn = 0
        for here, there in zip(route, route[1:]):
            if here is there:
                turn += 1
                self.zones[here.name, turn] += 1
                continue
            link = network.connection_between(here, there)
            for used_turn in range(turn + 1, turn + there.entry_cost + 1):
                self.links[link.name, used_turn] += 1
                self.zones[there.name, used_turn] += 1
            turn += there.entry_cost


class SpaceTimeFinder(PathFinder):
    """Plan one timed route per drone (see the module docstring)."""

    def __init__(self, nb_drones: int) -> None:
        """Remember how many routes to plan.

        Args:
            nb_drones: Number of drones to route.
        """
        self.nb_drones = nb_drones

    def find_paths(self, network: Network) -> list[list[Zone]]:
        """Return one timed route per drone, in drone id order.

        Args:
            network: The network to plan on.

        Returns:
            One route per drone. A zone repeated in a route means the
            drone waits there for one turn.

        Raises:
            NoPathError: If the end zone cannot be reached.
        """
        distances = self._distances_to_end(network)
        if network.start.name not in distances:
            raise NoPathError(
                f"no path from {network.start.name!r} to "
                f"{network.end.name!r}"
            )
        first, turns = self._plan_all(network, distances, Counter())
        crowd = Counter(
            there.name
            for route in first
            for here, there in zip(route, route[1:])
            if here is not there
        )
        second, turns_again = self._plan_all(network, distances, crowd)
        return second if turns_again < turns else first

    def _plan_all(
        self,
        network: Network,
        distances: dict[str, int],
        crowd: Counter[str],
    ) -> tuple[list[list[Zone]], int]:
        """Plan every drone once.

        Args:
            network: The network to search.
            distances: Turns left to the end, per zone.
            crowd: How much to avoid each zone when arrival ties.

        Returns:
            The routes in drone id order, and the turn the last drone
            arrives.
        """
        table = ReservationTable()
        window = 2 * distances[network.start.name] + len(network.zones)
        routes: list[list[Zone]] = []
        arrival = 0
        for _ in range(self.nb_drones):
            # A drone leaving much earlier than this cannot arrive any
            # sooner than the drone before it, so skip those turns.
            earliest = max(0, arrival - window)
            route, arrival = self._earliest_route(
                network, table, distances, crowd, earliest
            )
            table.book_route(network, route)
            routes.append(route)
        return routes, arrival

    def _earliest_route(
        self,
        network: Network,
        table: ReservationTable,
        distances: dict[str, int],
        crowd: Counter[str],
        earliest: int,
    ) -> tuple[list[Zone], int]:
        """Return the earliest-arriving route for one more drone.

        The heap orders states by the turn they could reach the end at
        best, so a move costing two turns is handled like any other.
        Ties go to the least crowded route, then to the least effort: a
        priority zone costs less than other zones, and any move costs
        more than waiting, so a drone never moves for nothing.

        Args:
            network: The network to search.
            table: What earlier drones already booked.
            distances: Turns left to the end, per zone.
            crowd: How much to avoid each zone when arrival ties.
            earliest: The first turn this drone may leave the start.

        Returns:
            The route, with a repeated zone for each waiting turn, and
            the turn it reaches the end zone.

        Raises:
            NoPathError: If the search runs out of states.
        """
        parents: dict[State, State] = {}
        best = earliest + distances[network.start.name]
        # (best arrival, crowding, effort, turn, zone name, parent)
        heap = [(best, 0, 0, earliest, network.start.name, NO_PARENT)]

        while heap:
            _, crowding, effort, turn, name, parent = heapq.heappop(heap)
            state = (name, turn)
            if state in parents:
                continue
            parents[state] = parent
            zone = network.zones[name]
            if zone is network.end:
                route = self._rebuild(network, parents, state)
                return [network.start] * earliest + route, turn

            steps = self._moves(network, table, distances, zone, turn)
            for there, arrival, extra in steps:
                # Only entering a zone adds crowding, not waiting in it.
                crowded = 0 if there is zone else crowd[there.name]
                heapq.heappush(heap, (
                    arrival + distances[there.name],
                    crowding + crowded,
                    effort + extra,
                    arrival,
                    there.name,
                    state,
                ))
        raise NoPathError("no route left for a drone")

    @staticmethod
    def _moves(
        network: Network,
        table: ReservationTable,
        distances: dict[str, int],
        zone: Zone,
        turn: int,
    ) -> list[tuple[Zone, int, int]]:
        """Return every legal next step for a drone in ``zone``.

        Waiting is a step too: the drone stays in ``zone`` one more
        turn, if the zone still has room then.

        Args:
            network: The network to search.
            table: What earlier drones already booked.
            distances: Turns left to the end, per zone.
            zone: Where the drone is at the end of ``turn``.
            turn: The current turn.

        Returns:
            ``(next zone, turn it is reached, effort)`` for each step.
            Effort is 0 for waiting, 1 for a priority zone and 2 for
            any other zone.
        """
        steps: list[tuple[Zone, int, int]] = []
        if table.zone_is_free(zone, turn + 1):
            steps.append((zone, turn + 1, 0))
        for link in network.neighbors(zone):
            neighbor = link.other_end(zone)
            if neighbor.name not in distances:
                continue
            if table.can_move(link, neighbor, turn + 1):
                effort = 1 if isinstance(neighbor, PriorityZone) else 2
                steps.append((neighbor, turn + neighbor.entry_cost, effort))
        return steps

    @staticmethod
    def _distances_to_end(network: Network) -> dict[str, int]:
        """Return the fewest turns from each zone to the end zone.

        Other drones are ignored. A zone missing from the result cannot
        reach the end: it is blocked, or only blocked zones link it to
        the rest of the map.

        Args:
            network: The network to measure.

        Returns:
            A map of zone name to remaining turns.
        """
        distances = {network.end.name: 0}
        heap = [(0, network.end.name)]
        while heap:
            distance, name = heapq.heappop(heap)
            if distance > distances[name]:
                continue
            zone = network.zones[name]
            for link in network.neighbors(zone):
                other = link.other_end(zone)
                if not other.is_accessible:
                    continue
                through = distance + zone.entry_cost
                if through < distances.get(other.name, through + 1):
                    distances[other.name] = through
                    heapq.heappush(heap, (through, other.name))
        return distances

    @staticmethod
    def _rebuild(
        network: Network, parents: dict[State, State], state: State
    ) -> list[Zone]:
        """Walk parent links back from ``state`` into a zone list.

        Args:
            network: The network holding the zones.
            parents: Map of each state to the state it came from.
            state: The final state, at the end zone.

        Returns:
            The route from the start zone to the end zone.
        """
        names: list[str] = []
        while state != NO_PARENT:
            names.append(state[0])
            state = parents[state]
        names.reverse()
        return [network.zones[name] for name in names]
