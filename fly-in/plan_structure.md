# Fly-in — Development Plan

> Drone routing simulation · Python 3.10+ · OOP · fully type-safe (flake8 + mypy)
> Goal: move all drones start → end in the fewest turns, and reach the **bonus part**.
> Last full check: 2026-10-31, against subject v1.4 and the 10 official maps (results in §3).

---

## 0. File reference — what each folder/file contains

The skeleton exists on disk. Files or methods marked *(Step N)* don't exist yet.

### Root

| File | Contains |
|---|---|
| `main.py` | Entry point. Wires the pipeline: `Parser` → `PathFinder` → `Scheduler` → `Simulator` → `Visualizer`. Catches `FlyInError` so failures print a clean message instead of crashing. |
| `Makefile` | `install`, `run`, `debug` (pdb), `clean`, `lint` (flake8 + the exact mandatory mypy flags), `lint-strict` (`mypy --strict`), `test` (pytest). |
| `setup.cfg` | flake8 + mypy configuration (line length, ignore rules, strict flags). |
| `.gitignore` | Excludes `__pycache__`, `.mypy_cache`, venvs, editor files. |
| `requirements.txt` | Dev dependencies: flake8, mypy, pytest. |
| `README.md` | Required 42 submission README: italic first line, Description, Instructions, Resources (+ AI usage), algorithm write-up, visualization write-up. |
| `maps/` | `example.map`, our own easy and bad maps. The official maps move here in Step 5. |
| `tests/` | pytest suite. Not submitted (subject III.3), but it's how every step is verified. |

### `models/` — the domain objects (the "nouns" of the simulation)

| File | Contains |
|---|---|
| `zone.py` | `Zone` abstract base (`name`, `x`, `y`, `color`, `max_drones`, `unlimited`, `occupants`, abstract `entry_cost`, `is_accessible`, `has_capacity()`). Subclasses `NormalZone`, `RestrictedZone`, `PriorityZone`, `BlockedZone`. `ZoneFactory.build()` turns a parsed `zone=<type>` string into the right subclass (raises on unknown type). Start and end are not subclasses: they are zones with `unlimited=True`. |
| `connection.py` | `Connection`: an undirected edge (`zone_a`, `zone_b`, `max_link_capacity`, `in_transit` counter). `name` is the connection as written in the map (`zoneA-zoneB`), printed during restricted transit. `other_end(zone)` and `can_traverse()`. |
| `network.py` | `Network`: the graph — `zones: dict[str, Zone]`, `adjacency: dict[str, list[Connection]]`, `start`/`end` properties, `add_zone`, `add_connection` (rejects duplicates/self-loops), `neighbors(zone)`, `connection_between(a, b)` *(Step 6)*. No graph library — all traversal is hand-written elsewhere. |
| `drone.py` | `Drone`: `id`, `position` (a `Zone`, or a `Connection` while flying), `path`, `path_index`, `remaining_transit`, `state` (`DroneState` enum: `AT_ZONE` / `IN_TRANSIT` / `DELIVERED`), `label` (`D<id>`), `next_zone` (peek), `advance()` (commit), `begin_transit()`. |

### `parsing/` — text → objects, strictly

| File | Contains |
|---|---|
| `errors.py` | `FlyInError` base class; `ParseError` (carries a line number), `NoPathError`, `SimulationError`. |
| `parser.py` | `Parser.parse_file(path)` opens the file (context manager) and calls `parse_lines(lines)`, which implements the full grammar: `nb_drones:` line, `start_hub:`/`end_hub:`/`hub:` zone lines, `connection:` lines, `#` comments, and `_parse_metadata()` for `[key=value ...]` blocks. Raises `ParseError` with line number on any problem. |

### `pathfinding/` — which routes the drones take (no graph libraries allowed)

| File | Contains |
|---|---|
| `pathfinder.py` | `PathFinder` abstract base: `find_paths(network) -> list[list[Zone]]` (Strategy pattern — the simulator doesn't care which finder produced the paths). |
| `bfs_flow.py` | `BFSFlowFinder` — the baseline strategy: one shortest path by number of connections, shared by all drones. It ignores turn costs, so it isn't the final planner; the tests use it. Its docstrings still describe multi-path flow and get corrected in Step 6. |
| `space_time.py` | *(Step 6)* `ReservationTable` and `SpaceTimeFinder` — the real planner: one timed route per drone, found through (zone, turn) states. See §3. |
| `mincost_flow.py` | Empty stub from the old plan. Deleted in Step 6. |

### `simulation/` — executing the routes, turn by turn

| File | Contains |
|---|---|
| `scheduler.py` | `Scheduler.assign(network, paths, nb_drones)` — creates the drones and gives each one its route. `path_cost(path)` sums `entry_cost` over a path. |
| `simulator.py` | `Simulator.run()`/`step()` — the deterministic turn engine: frees leaver capacity before validating enterers, enforces zone/connection capacity, handles restricted transit, breaks ties by drone id, emits the formatted turn line, marks arrivals as delivered. It is the rule enforcer: it never trusts the plan. |

### `visualization/` — showing the run to a human

| File | Contains |
|---|---|
| `visualizer.py` | `Visualizer` abstract base: `show_network()`, `show_turn()`, `show_summary()`. Kept decoupled so rendering never affects correctness. |
| `terminal.py` | `TerminalVisualizer` — ANSI-colored terminal output driven by each zone's `color` metadata, zone states per turn, and end-of-run secondary metrics (turns, drones/turn, avg turns/drone, total path cost). |

---

## 0.5 Step-by-step TODO (build order)

Work top to bottom. Keep `make lint` and the tests green after every checked
step — each one should end in something observable, not just code that
compiles. Commit after each step that goes green, so a mistake (or `git restore`)
can never cost more than one step. Don't start a step until the previous one is
verified.

The tracker follows the same steps: https://claude.ai/artifact/9iTN7ZXZP9fY8mvSC1wgZK

- [x] **Step 1 — Zones & factory** (`models/zone.py`)
  - [x] Implement `ZoneFactory.build()`: look up `zone_type` in `_TYPES`, raise `ParseError` on an unknown type.
  - [x] Verify: unit test that `build("restricted", …).entry_cost == 2` and `build("bogus", …)` raises.

- [x] **Step 2 — Network wiring** (`models/network.py`, `models/connection.py`)
  - [x] Implement `add_zone` (reject duplicate names, reject a second start/end).
  - [x] Implement `add_connection` (both zones must exist, reject `a-b`/`b-a` duplicates and self-loops).
  - [x] Implement `Connection.can_traverse()`.
  - [x] Verify: build a tiny network by hand in a test, check `neighbors()`.

- [x] **Step 3 — Parser** (`parsing/parser.py`) — first big milestone
  - [x] Implement `_parse_metadata()` for `[key=value ...]` blocks.
  - [x] Implement `parse_lines()`: `nb_drones:` first, then zone lines (via `ZoneFactory`), then `connection:` lines; ignore `#`/blank lines; enforce exactly one start and one end; attach the line number to every error.
  - [x] Verify: `python main.py maps/example.map` parses without error.
  - [x] Write your own bad maps (missing start, duplicate connection, capacity 0, bad zone type, self-loop, `nb_drones` not first) and confirm each raises a clean `ParseError`. A missing start has no single line to point at, so its message has no line number. A disconnected end is not a parse error: it is a `NoPathError` from pathfinding, covered in `tests/test_bfs_flow.py`.
  - Fixed along the way: `StartZone`/`EndZone` subclasses couldn't actually be produced by the parser (it only builds zones from the `zone=` tag). Replaced with an `unlimited: bool` flag on the base `Zone`, set by the parser when the line keyword is `start_hub`/`end_hub`. This also correctly allows a start/end zone to carry a real entry-cost type if ever tagged one.
  - Fixed along the way: `mypy .` was crashing on a stray global `numpy` install pulled in transitively via `pytest`'s optional `TYPE_CHECKING` import (`numpy` is not a project dependency). Added an isolated `.venv/` (gitignored) with only flake8/mypy/pytest — run tooling through it, e.g. `./.venv/Scripts/python.exe -m pytest -q`.

- [x] **Step 4 — BFS single path + minimal simulator**
  - [x] `BFSFlowFinder._bfs()` returning one shortest path.
  - [x] Trivial `Scheduler.assign()` putting every drone on that one path.
  - [x] `Simulator.step()`/`run()` for the no-conflict case (no capacity contention).
  - [x] Verify: `maps/easy_linear.map` produces the exact expected `D1-… D2-…` schedule in 6 turns. This is our own 5-connection map, not the official linear map (3 connections, 4 turns).
  - Design change along the way: `Drone.step()` (self-contained per-drone advance) doesn't fit the turn model — the simulator needs a *global* view of every drone's intended move before it can validate capacity (leavers must free a zone before entrants into it are checked, across *all* drones at once, in the same turn). Replaced with `Drone.next_zone` (peek) + `Drone.advance()` (commit), orchestrated by `Simulator.step()`.
  - Known, intentional gap until Step 5: restricted-zone multi-turn transit is not yet implemented — a move into a `RestrictedZone` is currently (incorrectly) treated as an instant 1-turn move.
  - `main.py` is fully wired end-to-end (parse → find path → assign → simulate → print lines); only the visualizer hookup remains for Step 7.

- [ ] **Step 5 — Full turn rules** — the correctness milestone
  The two-phase `step()` stays as it is: all movers leave first, then enter in id order. That is what makes two drones swapping zones legal (VII.3). Everything here extends it.
  - [x] **5.1 `Drone`:** keep `remaining_transit`. `advance()` sets the state back to `AT_ZONE` unless delivered. New `begin_transit(connection, turns)` puts the drone on the connection with `remaining_transit = turns - 1`.
  - [x] **5.2 `Simulator.step()`:** flying drones are handled first: each one counts in `connection.in_transit`, `remaining_transit` goes down, and at 0 it lands with `advance()`. A flying drone is never checked for capacity, because at take-off (`entry_cost > 1`) its destination was reserved by appending it to `occupants`.
  - [x] **5.3 Transit tests** in `tests/test_simulator.py`: take-off prints `D<id>-<connection>`, landing prints the zone on the next turn, `example.map` gives the known 12-turn schedule, restricted end zone, two restricted zones in a row, `max_drones=2` with link capacity 2, a connection written backwards in the map, a landing drone still using the link, a taken zone blocking take-off even when the link has room.
  - [x] **5.4 Guards:** add `SimulationError(FlyInError)`. `run()` raises when a turn moves nobody; it used to loop forever. `step()` raises when a blocked drone's zone is already full; it used to overfill silently (two drones in a `max_drones=1` zone, reproduced). One path can't trigger this, because lower ids lead, and planned routes never block, so a guard is enough: `step()` doesn't need a redesign.
  - [x] **5.5 Parser fixes:** `parse_file` catches `UnicodeError` next to `OSError`: any non-UTF-8 file, even one `é` in a comment, used to end in a traceback, and the subject counts that as non-functional. `zone=blocked` is rejected on `start_hub`/`end_hub` (a blocked start used to run). The unused `InvalidMapError` is gone.
  - [x] **5.6 Official maps:** `maps_from_PDF/easy`, `medium`, `hard`, `challenger` and the README moved into `maps/` with `git mv`, content unchanged. `subject_flyin.pdf` is untracked and in `.gitignore` (it stays in the history of caec91f, already pushed).
  - [ ] **5.7 Referee** in `tests/test_referee.py` (not the simulator's code): a `Referee` class replays the lines `main.py` printed and checks every rule on its own: adjacency, connection names as the map wrote them, blocked zones, zone capacity including the take-off reservation, link capacity including landing drones, a multi-turn move lasts exactly `entry_cost` turns, nobody waits on a connection, every drone is delivered. Run on every map, every time, with its turn count, plus hand-made bad runs that prove each check fires.
  - [ ] **5.8 `make test`:** it fails today with 7 collection errors, because bare `pytest` can't import `models`. Change the rule to `$(PYTHON) -m pytest -q`. Also fix the Makefile comment's example `maps/easy_2.map`, which doesn't exist: use `maps/easy/01_linear_path.txt`.
  - [ ] Verify: flake8, mypy, tests and referee clean. Turn counts match the "BFS + transit" column in §3, including `03_priority_puzzle` at 13 turns, which misses its target of 12 until Step 6.

- [ ] **Step 6 — Space-time planner** (`pathfinding/space_time.py`, see §3)
  Replaces both the old BFS multi-path task and the old min-cost flow step. The core (6.1–6.7) is what meets every target and the Challenger; 6.8 and 6.9 are hardening.
  - [ ] **6.1 `Network.connection_between(a, b)`:** move `Simulator._connection_between` here, because the planner needs it too.
  - [ ] **6.2 Planned waits:** a repeated zone in a path means "stay one turn". `step()` sees `next_zone is position`, calls `advance()` and prints nothing.
  - [ ] **6.3 `Scheduler.assign`:** give each drone `paths[index % len(paths)]`, so one shared BFS path and one route per drone both work.
  - [ ] **6.4 `ReservationTable`:** who holds which zone and link on which turn. `zone_is_free`, `can_move` (checks every turn of the movement, so 2-turn moves need no special case), `book_route`. Unit-test it alone.
  - [ ] **6.5 `SpaceTimeFinder(nb_drones)`:** for each drone, search (zone, turn) states for the earliest arrival. It's your BFS with time added to the state: `parents` and the rebuild are the same idea. Waiting is a neighbor. A restricted move jumps 2 turns, so the queue becomes a `heapq` ordered by turn. Book the route, then plan the next drone. `nb_drones` goes to the constructor, so `PathFinder.find_paths(network)` keeps its signature.
  - [ ] **6.6 Tie-break:** among equal arrival turns, the least effort wins: priority zone 1, any other zone 2, waiting 0. A bonus for priority zones doesn't work: a drone bounces in and out of them to collect it. Test that a priority route beats an equal normal route.
  - [ ] **6.7 Wire it into `main.py`.** Verify with the referee and a test of every target: all 10 official maps must match the "Space-time" column in §3. Example: `example.map` goes from 12 turns to 6, with the drones using both routes.
  - [ ] **6.8 Second pass:** plan everything once, count how many drones entered each zone, plan again with "avoid crowded zones" as the first tie-break, and keep the better plan (the first one on a tie). Without this, an unlucky tie can queue every drone behind a route that crosses two free ones. It was 10 turns off the optimum on one random map; with the second pass, never more than 1.
  - [ ] **6.9 Speed for large drone counts:** compute each zone's distance to the end once, backwards from the end (a zone missing from it is a dead end or blocked, which also replaces the reachability check). Order the heap by `turn + distance`. Start each drone's search at `last arrival - window`, not turn 0, with `window = 2 * distance from start + number of zones`. Measure it (see §3).
  - [ ] **6.10 Edge-case maps** next to the bad ones: start directly linked to end, restricted end zone, two restricted zones in a row, disconnected end, route only through a blocked zone, two equal routes with one priority, drones needing the same link in opposite directions, 1000 drones.
  - [ ] **6.11 Clean up:** delete `mincost_flow.py` and its import in `tests/test_smoke.py`. Correct the docstrings in `bfs_flow.py` and `scheduler.py` that describe multi-path flow. Correct the `Simulator` class docstring.
  - [ ] Verify: referee clean on every map, same output on repeated runs (nothing may depend on set order).

- [ ] **Step 7 — Visualization** (mandatory, VII.1; see §6)
  - [ ] **7.1 `show_network`:** zones in their map colors with type and capacity, connections with capacity, a legend.
  - [ ] **7.2 `show_turn` with zone states:** VII.1 requires them, and the current signature only receives the movement line, so add a `network` parameter. Show `occupied/max` and drone ids per zone, and drones in flight. `occupants` also holds drones still flying toward the zone: compare `drone.position is zone`.
  - [ ] **7.3 Hook:** `Simulator.run()` takes an optional `visualizer` and calls it after each `step()`. Existing calls to `run()` keep working.
  - [ ] **7.4 `show_summary`:** turns, drones moved per turn, average turns per drone, total path cost. This needs each drone's arrival turn recorded, and `path_cost` must skip waits.
  - [ ] **7.5 Colors:** the official maps use 17 color names and `ANSI_COLORS` has 4 of them. Missing: black, brown, crimson, cyan, darkred, gold, lime, magenta, maroon, orange, purple, rainbow, violet. Use 256-color codes. `black` must stay readable on a dark terminal, and `rainbow` needs a chosen look. Unknown names keep falling back to plain text.
  - [ ] **7.6 Keep the format exact:** the `D<id>-…` lines stay byte-exact, with no colors and no prefix. When stdout isn't a terminal (`sys.stdout.isatty()`), print only those lines, so the output can be piped into a checker.
  - [ ] Verify: watch a colored run end-to-end; `python main.py <map> | cat` prints only plain lines and the referee accepts them.

- [ ] **Step 8 — Polish & defense**
  - [x] **8.1 README, do now:** add the final period to the first line (the PDF sets it in italics, so it is part of the required line), and correct the AI usage section: AI wrote the first version of Steps 1–4.
  - [ ] **8.3** Full docstrings (PEP 257), type hints everywhere, `make lint-strict` clean.
  - [ ] **8.4 Small cleanups:** remove `NotImplementedError` from the `except` in `main.py` (no stubs left), the old `# TODO` comments, and the ineffective `[mypy-numpy]` sections in `setup.cfg`. Use `$(PYTHON) -m pip` in the Makefile, so `pip` can't belong to another Python.
  - [ ] **8.5 Integer parsing (low priority):** `int()` accepts `1_0`, `+3` and non-ASCII digits, so `nb_drones: 1_0` parses as 10. Reject them, in coordinates too.
  - [ ] **8.6 Submission repo:** `Makefile`, `main.py` and `README.md` at the root of the repo you submit (today the git root is `42_work_git`, with the project in a subfolder). Leave out `tests/`, `plan_structure.md` and `subject_flyin.pdf`. Removing `tests/` also means removing the `test` rule and `pytest` from `requirements.txt`. Ask a peer whether `models/` and the other code folders are fine under "place all your files at the root".
  - [ ] **8.7 Fresh clone on a 42 machine:** `make install`, `lint`, `lint-strict`, `run`, `debug`, `clean`.
  - [ ] **8.8 Defense rehearsal** (§11), without notes.

- [ ] **Step 9 — Bonus check and README (only after Steps 1–8 are solid and green)**
  - [ ] Confirm all provided maps meet or beat their reference targets on your final code.
  - [ ] Confirm the Challenger map ("Impossible Dream", 25 drones) beats 45 turns: 43 is expected, and it is the proven minimum.
  - [ ] **README: written by you, as the very last step.** Algorithm choices, complexity, visualization, resources, AI usage, best turn count per map.

---

## 1. Understanding the problem

At its core, Fly-in is a **flow-over-time / scheduling** problem (the classic 42 "lem-in" reimagined with drones), with several twists that make it harder than the original:

| Feature | Effect on the algorithm |
|---|---|
| `normal` zone | entering costs **1 turn** |
| `restricted` zone | entering costs **2 turns**; drone sits on the connection for 1 turn, *must* arrive next turn (can't wait extra) |
| `priority` zone | costs 1 turn but should be **preferred** (soft bias, not a hard rule) |
| `blocked` zone | never entered / never traversed |
| `max_drones=N` | a zone can hold up to **N** drones at once (default 1) |
| `max_link_capacity=N` | up to **N** drones can traverse a connection simultaneously (default 1), both directions together |
| start / end | **unlimited** capacity |

So compared to plain lem-in (unit-capacity, unit-cost, vertex-disjoint paths), we need to handle **moves of different lengths** and **capacities on both zones and connections**. What matters is not only which routes exist, but **who uses what on which turn**.

**The winning insight:** the number of turns is *not* just the shortest path length. It's the **makespan** of pipelining N drones through the network. Sometimes using one extra, slightly-longer path lowers total turns; sometimes it doesn't. And the time dimension matters: two drones can share a single-capacity start and then take turns on two parallel routes, which no fixed set of disjoint paths can express.

### Decisions (these were open questions)

- **Connection name in output.** `Connection.name`, exactly as written in the map, even when flying the other way: `connection: roof1-hub` prints `D1-roof1-hub`. The subject calls `<name1>-<name2>` the connection's name.
- **Restricted cost.** It belongs to the move *into* the restricted zone: the destination decides, whichever side the drone comes from.
- **Capacity during transit: the conservative reading.** The destination is reserved from take-off, and the link counts on both the take-off turn and the landing turn. A schedule valid under this reading is also valid under the looser one (only the drones sitting on the link at the end of a turn count), so it can't be judged illegal. The looser reading could finish two maps sooner (circular loop 10 instead of 15, priority puzzle 6 instead of 7), but every target is met without it, and the subject's ≤15 for the circular loop is exactly what this reading gives.
- **Multi-turn moves are general.** Nothing assumes "2": the length comes from `entry_cost`. Restricted can cost 3, or a new zone type 4, without touching the simulator or the planner.
- **"Any number of drones".** Nothing is hard-coded, and speed is measured in §3. Thousands of drones take a minute or more on any algorithm: with one bottleneck link there are as many turns as drones, so the simulator alone grows with the square of the drone count.

---

## 2. Target architecture (OOP)

Keep classes small and single-purpose so you can explain each one in review.

```
fly-in/
├── Makefile
├── README.md
├── .gitignore
├── main.py                 # entry point: parse → plan → simulate → visualize
├── models/
│   ├── zone.py             # Zone hierarchy + ZoneFactory
│   ├── connection.py       # Connection (edge + capacity)
│   ├── network.py          # Graph: zones + adjacency, lookups, neighbors
│   └── drone.py            # Drone: id, position, path, state
├── parsing/
│   ├── parser.py           # File → Network + nb_drones, line-accurate errors
│   └── errors.py           # ParseError, NoPathError, SimulationError
├── pathfinding/
│   ├── pathfinder.py       # abstract PathFinder (Strategy pattern)
│   ├── bfs_flow.py         # baseline: one shortest path by connection count
│   └── space_time.py       # the planner: one timed route per drone
├── simulation/
│   ├── scheduler.py        # creates drones, gives each its route
│   └── simulator.py        # turn-by-turn engine, enforces all rules
├── visualization/
│   ├── visualizer.py       # abstract Visualizer
│   └── terminal.py         # colored terminal output
└── maps/                   # your own test maps + the provided ones
```

### Class design (this is where "completely object-oriented" is proven)

**Zone hierarchy.**
- `Zone` (abstract base): `name`, `x`, `y`, `color`, `max_drones`, `unlimited`, `occupants`.
  - `entry_cost` → abstract property returning the turn cost.
  - `is_accessible` → bool.
  - `has_capacity()` → checks occupancy against `max_drones`, always True when `unlimited`.
- Subclasses: `NormalZone` (cost 1), `RestrictedZone` (cost 2), `PriorityZone` (cost 1, preferred), `BlockedZone` (inaccessible). Start and end are a flag, not subclasses: role and zone type are separate axes.
- A small `ZoneFactory` maps the parsed `zone=<type>` string to the right subclass and raises on unknown types.

**Connection**: `zone_a`, `zone_b`, `max_link_capacity`, live traversal count per turn. Provides `other_end(zone)` and `can_traverse()`.

**Network (Graph)**: dict `name → Zone`, adjacency `name → list[Connection]`. One `Connection` object is stored under both endpoints. Methods: `add_zone`, `add_connection` (rejects duplicates a-b == b-a), `neighbors(zone)`, `connection_between(a, b)`, `start`, `end`. **No graph libraries** (networkx/graphlib forbidden). `heapq` and `collections` are general-purpose, not graph logic.

**Drone**: `id`, `position` (a `Zone` or a `Connection` while in transit), `remaining_transit`, assigned `path`, `state`. `next_zone` (peek) + `advance()` (commit) + `begin_transit()`: the simulator decides, the drone executes.

**PathFinder (Strategy)**: `BFSFlowFinder` and `SpaceTimeFinder` are interchangeable behind `find_paths(network)`. Both return a list of paths: BFS one shared path, the planner one timed route per drone.

**Custom exceptions** in `parsing/errors.py` so failures are clean (spec: unhandled crash = non-functional).

---

## 3. Algorithm strategy (the heart of the project)

### Why the old two-tier plan was dropped

The old plan was BFS multi-path for easy and medium maps, then min-cost flow with node splitting and a search over the flow value for hard maps and the bonus. Running the 10 official maps (private prototypes, every output replayed by an independent rule checker, optimum proven with an integer-programming solver that is not part of the project) showed that this was wrong:

| Map | Drones | Target | BFS + transit | Weighted single path | Old plan (min-cost flow) | Space-time | Proven best |
|---|---:|---:|---:|---:|---:|---:|---:|
| easy 1 linear path | 2 | 6 | 4 | 4 | 4 | **4** | 4 |
| easy 2 simple fork | 4 | 8 | 6 | 6 | 4 | **4** | 4 |
| easy 3 basic capacity | 4 | 6 | 4 | 4 | 4 | **4** | 4 |
| medium 1 dead end trap | 5 | 12 | 8 | 8 | 8 | **8** | 8 |
| medium 2 circular loop | 6 | 15 | 15 | 15 | 15 | **15** | 15 |
| medium 3 priority puzzle | 5 | 12 | 13 ✗ | 8 | 7 | **7** | 7 |
| hard 1 maze nightmare | 8 | 30 | 13 | 13 | 13 | **13** | 13 |
| hard 2 capacity hell | 12 | 35 | 16 | 16 | 16 | **16** | 16 |
| hard 3 ultimate challenge | 15 | 45 | 41 | 26 | 26 | **26** | 26 |
| challenger impossible dream | 25 | 45 | 67 ✗ | 67 ✗ | 67 ✗ | **43** | 43 |

- **The hard maps never needed heavy machinery.** Plain BFS plus restricted transit already meets all three. Each one has a single-capacity link or zone that every drone must cross, so extra paths can't help: the proven best equals the best single path.
- **Min-cost flow can't win the bonus it was planned for.** `start-gate_hell1` has capacity 1, so the static max flow is 1, so it only ever sees one path: 19 turns + 2 × 24 for the restricted zones = 67. The real answer shares that link, then alternates drones between two parallel routes: 19 + 24 = 43. A flow fixed per turn can't express "take turns". It also overestimates restricted zones, which pass one drone every 2 turns when `max_drones=1`.
- **What actually decides the mandatory targets** is turn costs (VII.1 requires them) and the time dimension.

### The algorithm: space-time planning

Plan the drones one at a time, in id order. Each drone finds its earliest arrival around what earlier drones already booked, books its route, and the next one plans around that.

```
table = empty ReservationTable
for each drone:
    search states (zone, turn), starting at (start, 0):
        wait    -> (zone, turn + 1)                   if the zone stays free
        move    -> (neighbor, turn + entry_cost)      if the link and the zone
                                                      stay free for every turn
                                                      of the movement
    first state popped at the end zone = earliest arrival
    book every zone and link of that route in the table
```

This one idea covers every line of VII.1:

| VII.1 requirement | How it's covered |
|---|---|
| Distribution across multiple paths | a drone takes another route as soon as that arrives sooner |
| Strategic waiting | waiting is a move in the search |
| Avoiding conflicts and deadlocks | nobody books a taken slot; a route is complete before the next drone plans, and waiting at the unlimited start is always possible |
| Movement costs | a restricted move advances the clock by 2 |
| Priority zones | the effort tie-break (6.6) |
| Zone and connection capacity | checked in the table, enforced again by the simulator |
| Adaptable to each map | nothing is map-specific; the second pass adapts to where the crowd went |

The planner's rules match the simulator's exactly: destination reserved from take-off, link used on both turns, leavers free capacity the same turn.

### Refinements

1. **Effort tie-break (6.6).** Priority zone 1, other zone 2, waiting 0. Any move costs more than waiting, so a drone never moves for nothing.
2. **Second pass (6.8).** The first plan shows where the crowd went. The second plan avoids those zones when that costs no time. Keep the better one. This is a simple form of negotiated congestion.
3. **Goal direction and window (6.9).** Order the heap by `turn + distance to end`, skip dead ends, and don't search departure turns too early to matter. Waiting at the start is always legal, so any plan this produces is still valid. The official maps' output didn't change.

### How sure are we?

Measured on the prototype. Measure again on your own code.

- **Official maps:** all 10 optimal, each planned in under 0.1 s.
- **1331 solvable random maps, compared with the exact optimum:** 0 invalid schedules, 0 stuck runs, exact on 1327 (99.7%), never more than 1 turn off. Planning is a heuristic, not a proof: don't claim it is always optimal.
- **Planner and simulator agree:** on every map above, the simulator's turn count equals what the planner promised, so no planned move is ever blocked.
- **Prototype size:** about 150 lines of code for the planner, without docstrings.

| Drones | Hardest map (ultimate) | Narrow map (Challenger) |
|---:|---:|---:|
| 100 | 2.4 s | 0.1 s |
| 300 | 6.6 s | 0.4 s |
| 1000 | 26 s | 2.7 s |
| 3000 | 99 s | |

### Complexity (for the README)

With V zones, E connections, n drones, T total turns and W the search window:

- One drone's search: at most `W · V` states and `W · (V + E)` heap pushes, so `O(W · (V + E) · log(W · (V + E)))`. All drones: `n` times that, twice.
- Simulation: `O(n · T)`, because each turn visits every drone.
- Memory: `O(n · T)` for the routes (each waiting turn is a list entry), plus the table, which grows with the total length of all routes.
- Paths are never recalculated during the run: each route is planned once, then executed.

---

## 4. The simulator (turn engine) — get the rules exactly right

This is where most points are lost. Process **one turn** as:

1. **Sort the drones:** flying, planned waits, and movers. Planned waits consume their path step and print nothing.
2. **Free space first:** every mover leaves its zone *this same turn* (spec: "drones moving out free up capacity for that same turn"). Reset the link counters.
3. **Flying drones go next:** each counts on its connection, `remaining_transit` goes down, and at 0 it lands. No capacity check: the place was reserved at take-off.
4. **Admit movers in ascending id:** a move is allowed only if the zone has room and the link isn't full this turn.
   - **Blocked:** the drone goes back to its zone and **waits**. If that zone is already full, raise `SimulationError`.
   - **Allowed, `entry_cost` 1:** the drone moves.
   - **Allowed, `entry_cost` above 1:** the drone joins the destination's `occupants` (the reservation) and goes on the connection. It **cannot** linger: it prints `D<id>-<connection>` until it lands.
5. **Emit the turn line:** space-separated `D<id>-<zone>` (or `-<connection>`), in id order, omitting drones that didn't move.
6. Mark arrivals at `end` as delivered; stop when all are delivered. If a turn moves nobody, raise `SimulationError`.

Keep the simulator **deterministic** — same input → same output. It stays the rule enforcer even though planned routes never conflict: a planner bug must show up as a clean error, never as an illegal turn.

---

## 5. Parser & error handling

Must be strict (spec lists these explicitly):
- First line `nb_drones: <positive int>` (comments and blank lines may come before it: every official map starts with a comment).
- Exactly **one** `start_hub:` and **one** `end_hub:`, neither blocked.
- Unique zone names; integer coords, possibly negative (the official maps use them); names may not contain dashes or spaces.
- Connections only reference already-defined zones; reject duplicates (`a-b` == `b-a`).
- Metadata blocks `[...]` syntactically valid; tags in any order; unknown `zone=` type → error.
- `max_drones` / `max_link_capacity` are positive integers.
- `#` comments ignored.
- **Any** parse error stops the program with a clear message giving **line number + cause**.
- A file that can't be read or decoded is a clean error too, never a traceback.

Checked on 2026-10-31: all 10 official maps parse with the current code. Valid: CRLF line endings, no final newline, tabs, zones declared after connections. `.txt` maps work like `.map`. `start_hub` and `end_hub` with `max_drones` lower than `nb_drones` must still hold every drone (`02_simple_fork` tests this: goal `max_drones=3`, 4 drones), and they do thanks to `unlimited`.

Use context managers for file handles, wrap parsing in try/except, and raise your custom `ParseError`. Build your **own edge-case maps** — the subject strongly recommends this and reviewers will test it (6.10). Evaluation maps may differ from the provided ones.

---

## 6. Visualization

Mandatory (VII.1 asks for drone movements **and zone states**). Start simple, upgrade if time allows.
- **Terminal (do this first):** ANSI colors driven by each zone's `color` metadata; render the turn line, zone occupancy, drones in flight, and a small legend. Also print the **secondary metrics** (turns, drones/turn, avg turns/drone, total path cost) — the subject encourages showing these to help reviewers.
- **Graphical (optional polish):** a simple view of zones at their `x,y`. Only after the mandatory part is fully green. Coordinates can be negative.
- Keep visualization **decoupled** from the simulator (an abstract `Visualizer` the simulator feeds events to) so it never affects correctness. The required `D<id>-…` lines must stay exact; colors and states are additional, and disappear when the output is piped.

---

## 7. Tooling & compliance checklist

- **Python 3.10+**, PEP 257 docstrings, `typing` hints everywhere, passes `mypy` (and aim for `mypy --strict` → the optional `lint-strict` rule).
- **Makefile** rules: `install`, `run`, `debug` (pdb), `clean`, `lint` (flake8 + the exact mypy flags from the subject), `lint-strict` (optional).
- `.gitignore` for `__pycache__`, `.mypy_cache`, venv, etc.
- **venv** for dependency isolation during dev. On this machine run everything through `.venv` (a global numpy breaks a bare `mypy`), and run pytest as `python -m pytest`.
- **Tests** with pytest (not graded and not submitted, but they'll save you): parser edge cases, the referee on every map, turn-count regression on the provided maps.
- **Commit after every green step.** `git restore` on a file wipes whatever was typed since the last commit.
- **README.md** (English) with: the exact required first italic line **including its final period**, `Description`, `Instructions`, `Resources` (incl. **how AI was used, for which tasks and parts**), plus your **algorithm choices / strategy** and **visualization** write-up.

---

## 8. Roadmap (milestones → bonus)

| Step | Deliverable | "Done" when |
|---|---|---|
| **0–4** ✅ | setup, model, parser, one path, minimal simulator | 34 tests green; bad maps fail cleanly |
| **5. Full turn rules** | restricted transit, guards, parser fixes, referee, official maps | every official map runs with zero rule violations |
| **6. Space-time planner** | one timed route per drone | **all 10 targets met**, Challenger in 43 |
| **7. Visualization** | colored terminal, zone states, secondary metrics | reviewer can *see* the simulation clearly |
| **8. Polish & defense** | docstrings, `mypy --strict`, submission repo | `make lint-strict` clean; rehearsal done |
| **9. BONUS + README** | confirmed results, then your README | every target met on the final code; Challenger under 45; README written last, by you |

**Bonus gate:** the bonus is only reviewed if the mandatory part is fully met — so don't call it done until Steps 0–8 are solid and green.

---

## 9. Bonus

- Both bonus goals come from Step 6, with no extra algorithm: match or beat every reference target, and solve the Challenger under 45 turns.
- 43 is the proven minimum for the Challenger: `start-gate_hell1` passes one drone per turn, so the 25th drone can't leave before turn 25, and the shortest route takes 19 turns: 24 + 19 = 43. Under the looser capacity reading the answer is also 43, so there is nothing left to gain.
- Record your own numbers in the README, on your final code.

---

## 10. Top risks / gotchas (where projects fail review)

1. **Restricted transit rule** — a drone can't wait on the connection, so its destination is reserved at take-off.
2. **Capacity ordering per turn** — leavers must free space *before* enterers are validated, in the same turn.
3. **Duplicate connections** (`a-b` vs `b-a`) are rejected at parse time. **Blocked zones stay in the network** (they must be displayed): the search skips them.
4. **Priority as a soft preference**, not a hard constraint — don't accidentally forbid non-priority paths, and don't reward entering priority zones.
5. **Determinism** — non-deterministic tie-breaks make bugs unreproducible and reviews painful.
6. **A hang counts as a failure too** — the simulator must stop with a clean error if nothing can move.
7. **Unhandled exceptions** — one traceback in review means non-functional. Try non-UTF-8 and binary files, not only wrong syntax.
8. **mypy under `--strict`** — annotate generics (`dict[str, Zone]`, `list[Connection]`), avoid `Any`.
9. **"Explain / modify on the spot"** — see §11. Know each class well enough to edit it cold.

---

## 11. Defense preparation

### The subject's review questions

| Question | Answer to prepare |
|---|---|
| How efficient is your algorithm? | The numbers in §3, on your final code. |
| Can it work with a large number of drones? | Yes: the speed table in §3. Be honest about the limit: time grows with drones × turns. |
| What is the complexity? | §3, and be able to derive it, the way you did for BFS. |
| Are you recalculating or caching paths? | Each route is planned once, before the run; the distance table is computed once; the simulator never replans. |
| How does it impact memory usage? | `O(n · T)` for the routes; a waiting turn is one list entry. |
| How does your visual representation enhance understanding? | Zone states and drones in flight show *why* a drone waits, which the movement lines alone can't show. |
| Can it meet the performance benchmarks? | The table in §3. |
| What optimizations did you implement? | Tie-break, second pass, goal direction, search window. Say what each one changed. |
| Can you beat the 45-turn record? | 43, and why it can't go lower (§9). |

### Questions a peer will likely ask

- Why is restricted 2 turns in the output if the subject's example shows `D1-roof1` on turn 1? That example only shows the format: it lists 2 drones while the map has 5. Rule VII.3 is explicit.
- Why 15 turns on the circular loop and not 10? The conservative capacity reading (§1).
- Why not min-cost flow? §3: the table and the Challenger argument.
- Is your planner always optimal? No: it's a heuristic, exact on 99.7% of tested random maps and never more than 1 turn off.
- Why can't drones deadlock? Each route is complete before the next drone plans, and waiting at the start is always possible.
- Show that the project is object-oriented: abstract classes (`Zone`, `PathFinder`, `Visualizer`), inheritance, the Factory, the Strategy.

### Live modifications to rehearse

Time yourself: each should take a few minutes.

- Restricted zones cost 3 turns (one line in `RestrictedZone.entry_cost`).
- A new zone type with its own cost (a subclass plus one `ZoneFactory._TYPES` entry).
- Print the turn number on each line, or change the output format.
- Add a metadata key, or a new parser rule.
- Change the tie-break: prefer the highest drone id, or ignore priority zones.
- Add a metric to `show_summary`.
- Store new information on `Drone` and display it.
