_This project has been created as part of the 42 curriculum by mrida._

# Fly-in

## Description

Fly-in is a drone-routing simulation. Given a network of connected
zones with a unique start and end, the program schedules a fleet of
drones from start to end in the **fewest possible simulation turns**,
while respecting zone types (normal, restricted, priority, blocked),
zone capacities (`max_drones`) and connection capacities
(`max_link_capacity`).

At its core this is a flow-over-time / scheduling problem: the number
of turns is the *makespan* of pipelining N drones across a chosen set
of paths, not simply the length of the shortest path.

## Instructions

Requires **Python 3.10+**.

```sh
make install        # install dev dependencies (flake8, mypy, pytest)
make run MAP=maps/example.map   # run the simulation on a map
make debug MAP=maps/example.map # run under pdb
make lint           # flake8 + mypy (mandatory checks)
make lint-strict    # flake8 + mypy --strict (optional, stricter)
make test           # run the test suite
make clean          # remove caches and __pycache__
```

The program reads a map file and prints, one line per turn, the
space-separated drone movements (`D<id>-<zone>`, or
`D<id>-<connection>` while a drone is mid-transit toward a restricted
zone), ending when every drone has reached the end zone.

## Project layout

```
main.py            entry point: parse -> solve -> simulate -> visualize
models/            Zone hierarchy, Connection, Network graph, Drone
parsing/           strict map parser + custom errors
pathfinding/       BFS multi-path (baseline) and min-cost flow (advanced)
simulation/        drone-to-path scheduler + turn-by-turn engine
visualization/     abstract visualizer + colored terminal renderer
maps/              provided and custom test maps
tests/             pytest suite (not graded)
```

## Algorithm choices and implementation strategy

<!-- TODO: fill in as you implement. Outline of the intended design: -->
- **Parsing** builds a `Network` of `Zone` objects (a small class
  hierarchy per zone type, created by a `ZoneFactory`) and validates
  the file strictly, reporting the line number on any error.
- **Baseline pathfinding** uses hand-written BFS to find edge-disjoint
  paths (Edmonds-Karp style augmentation), then a greedy scheduler
  spreads drones across them to balance the makespan.
- **Advanced pathfinding** models zone capacity via node splitting and
  restricted-zone weights via edge costs, solved with min-cost
  max-flow (Dijkstra + potentials). A search over the flow value picks
  the number of paths that yields the fewest turns.
- The **simulator** is a pure, deterministic turn engine that enforces
  the movement and occupancy rules exactly (leavers free capacity
  before enterers are validated; restricted transit must arrive next
  turn; capacities on both zones and connections are respected).

No third-party graph library is used (networkx / graphlib are
forbidden); all graph algorithms are implemented by hand.

## Visualization

<!-- TODO: describe the terminal (and any graphical) output and how it
helps a reviewer understand the simulation. -->
Colored terminal output driven by each zone's `color` metadata shows
per-turn drone movements and end-of-run secondary metrics (turns,
drones per turn, average turns per drone, total path cost).

## Resources

<!-- TODO: list references you actually used. -->
- Max-flow / min-cost-flow (Edmonds-Karp, successive shortest paths).
- The classic 42 "lem-in" project (the unweighted, unit-capacity
  ancestor of this problem).

### AI usage

<!-- Required by the subject: state for which tasks and which parts of
the project AI was used. -->
AI was used to scaffold the initial project structure (directory
layout, Makefile, lint/type-check configuration, class skeletons and
this README outline). AI also wrote the first version of the models,
parser, BFS, scheduler and simulator, and the author reviewed that
code to be able to explain it. Later changes were made with AI
guidance, and most of them were typed by the author.
