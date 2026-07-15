# Fly-in — Development Plan

> Drone routing simulation · Python 3.10+ · OOP · fully type-safe (flake8 + mypy)
> Goal: move all drones start → end in the fewest turns, and reach the **bonus part**.

---

## 0. File reference — what each folder/file contains

The skeleton already exists on disk (stubs raise `NotImplementedError` with a
`# TODO` describing the logic to fill in). This section is the map of it.

### Root

| File | Contains |
|---|---|
| `main.py` | Entry point. Wires the pipeline: `Parser` → `PathFinder` → `Scheduler` → `Simulator` → `Visualizer`. Catches `FlyInError` so failures print a clean message instead of crashing. |
| `Makefile` | `install`, `run`, `debug` (pdb), `clean`, `lint` (flake8 + the exact mandatory mypy flags), `lint-strict` (`mypy --strict`), `test` (pytest). |
| `setup.cfg` | flake8 + mypy configuration (line length, ignore rules, strict flags). |
| `.gitignore` | Excludes `__pycache__`, `.mypy_cache`, venvs, editor files. |
| `requirements.txt` | Dev dependencies: flake8, mypy, pytest (matplotlib optional, commented out). |
| `README.md` | Required 42 submission README: italic first line, Description, Instructions, Resources (+ AI usage), algorithm write-up, visualization write-up. |
| `maps/` | Map files: the provided example plus your own edge-case maps. |
| `tests/` | pytest suite (not graded, but catches regressions early). |

### `models/` — the domain objects (the "nouns" of the simulation)

| File | Contains |
|---|---|
| `zone.py` | `Zone` abstract base (`name`, `x`, `y`, `color`, `max_drones`, `occupants`, `entry_cost`, `is_accessible`, `has_capacity()`). Subclasses `NormalZone`, `RestrictedZone`, `PriorityZone`, `BlockedZone`, `StartZone`, `EndZone`. `ZoneFactory.build()` turns a parsed `zone=<type>` string into the right subclass (raises on unknown type). |
| `connection.py` | `Connection`: an undirected edge (`zone_a`, `zone_b`, `max_link_capacity`, `in_transit` counter). `name` gives the canonical id (`zoneA-zoneB`) used in output during restricted transit. `other_end(zone)` and `can_traverse()`. |
| `network.py` | `Network`: the graph — `zones: dict[str, Zone]`, `adjacency: dict[str, list[Connection]]`, `start`/`end` properties, `add_zone`, `add_connection` (rejects duplicates/self-loops), `neighbors(zone)`. No graph library — all traversal is hand-written elsewhere. |
| `drone.py` | `Drone`: `id`, `position` (a `Zone` or a `Connection` while mid-transit), `path`, `remaining_transit`, `state` (`DroneState` enum: `AT_ZONE` / `IN_TRANSIT` / `DELIVERED`), `label` (`D<id>`), `step()` — the per-drone turn state machine. |

### `parsing/` — text → objects, strictly

| File | Contains |
|---|---|
| `errors.py` | `FlyInError` base class; `ParseError` (carries a line number), `InvalidMapError`, `NoPathError`. |
| `parser.py` | `Parser.parse_file(path)` opens the file (context manager) and calls `parse_lines(lines)`, which implements the full grammar: `nb_drones:` line, `start_hub:`/`end_hub:`/`hub:` zone lines, `connection:` lines, `#` comments, and `_parse_metadata()` for `[key=value ...]` blocks. Raises `ParseError` with line number on any problem. |

### `pathfinding/` — which routes exist through the graph (no libraries allowed)

| File | Contains |
|---|---|
| `pathfinder.py` | `PathFinder` abstract base: `find_paths(network) -> list[list[Zone]]` (Strategy pattern — the simulator doesn't care which finder produced the paths). |
| `bfs_flow.py` | `BFSFlowFinder` — baseline: repeated BFS augmentation (Edmonds-Karp style) over a residual graph to find edge-disjoint paths respecting `max_link_capacity`. |
| `mincost_flow.py` | `MinCostFlowFinder` — advanced: node-splitting for `max_drones`, weighted edges for restricted/priority zones, min-cost max-flow via Dijkstra + Johnson potentials. |

### `simulation/` — turning routes into scheduled, turn-by-turn movement

| File | Contains |
|---|---|
| `scheduler.py` | `Scheduler.assign(network, paths, nb_drones)` — creates drones and distributes them across paths to balance the makespan. `path_cost(path)` sums `entry_cost` over a path. |
| `simulator.py` | `Simulator.run()`/`step()` — the deterministic turn engine: computes intended moves, frees leaver capacity before validating enterers, enforces zone/connection capacity, handles restricted 2-turn transit, breaks ties deterministically, emits the formatted turn line, marks arrivals as delivered. |

### `visualization/` — showing the run to a human

| File | Contains |
|---|---|
| `visualizer.py` | `Visualizer` abstract base: `show_network()`, `show_turn()`, `show_summary()`. Kept decoupled so rendering never affects correctness. |
| `terminal.py` | `TerminalVisualizer` — ANSI-colored terminal output driven by each zone's `color` metadata, plus end-of-run secondary metrics (turns, drones/turn, avg turns/drone, total path cost). |

---

## 0.5 Step-by-step TODO (build order)

Work top to bottom. Keep `make lint` and `make test` green after every checked
step — each one should end in something observable, not just code that
compiles. Don't start a step until the previous one is verified.

- [ ] **Step 1 — Zones & factory** (`models/zone.py`)
  - [ ] Implement `ZoneFactory.build()`: look up `zone_type` in `_TYPES`, raise `ParseError` on an unknown type.
  - [ ] Verify: unit test that `build("restricted", …).entry_cost == 2` and `build("bogus", …)` raises.

- [ ] **Step 2 — Network wiring** (`models/network.py`, `models/connection.py`)
  - [ ] Implement `add_zone` (reject duplicate names, reject a second start/end).
  - [ ] Implement `add_connection` (both zones must exist, reject `a-b`/`b-a` duplicates and self-loops).
  - [ ] Implement `Connection.can_traverse()`.
  - [ ] Verify: build a tiny network by hand in a test, check `neighbors()`.

- [ ] **Step 3 — Parser** (`parsing/parser.py`) — first big milestone
  - [ ] Implement `_parse_metadata()` for `[key=value ...]` blocks.
  - [ ] Implement `parse_lines()`: `nb_drones:` first, then zone lines (via `ZoneFactory`), then `connection:` lines; ignore `#`/blank lines; enforce exactly one start and one end; attach the line number to every error.
  - [ ] Verify: `python main.py maps/example.map` parses without error (temporarily print zone/connection counts in `main.py`).
  - [ ] Write your own bad maps (missing start, duplicate connection, capacity 0, bad zone type, self-loop, disconnected end) and confirm each raises a clean, line-tagged `ParseError`.

- [ ] **Step 4 — BFS single path + minimal simulator**
  - [ ] `BFSFlowFinder._bfs()` returning one shortest path.
  - [ ] Trivial `Scheduler.assign()` putting every drone on that one path.
  - [ ] `Simulator.step()`/`run()` for the no-conflict case (no capacity contention).
  - [ ] Verify: a linear map with 2 drones produces valid `D1-… D2-…` turn lines matching the required output format.

- [ ] **Step 5 — Multi-path + full turn rules** — the correctness milestone
  - [ ] `BFSFlowFinder.find_paths()`: multiple edge-disjoint paths via repeated augmentation.
  - [ ] `Scheduler.assign()`: balance drones across multiple paths (greedy, earliest-finish-first).
  - [ ] `Simulator.step()` full rules: leavers free capacity before enterers are validated; enforce `max_drones` and `max_link_capacity`; restricted zones commit to a 2-turn transit (must arrive next turn, no waiting mid-connection); deterministic tie-breaks on conflicts.
  - [ ] Verify: easy/medium maps hit their turn targets; add invariant tests (never exceed capacity, all drones eventually delivered).

- [ ] **Step 6 — Visualization**
  - [ ] Implement `TerminalVisualizer.show_network()`, `show_turn()`, `show_summary()` (incl. secondary metrics: turns, drones/turn, avg turns/drone, total path cost).
  - [ ] Wire the full pipeline in `main.py` (uncomment the pathfinder/scheduler/simulator/visualizer calls).
  - [ ] Verify: watch a full colored run end-to-end.

- [ ] **Step 7 — Advanced optimizer** (`pathfinding/mincost_flow.py`)
  - [ ] Node-splitting for `max_drones` (`v_in`/`v_out`).
  - [ ] Weighted edges (restricted = 2, normal/priority = 1, priority tie-break bias).
  - [ ] Min-cost max-flow via Dijkstra + Johnson potentials.
  - [ ] Flow-value search: simulate for each feasible flow value `f`, keep the best makespan.
  - [ ] Verify: hard maps meet their targets (≤30 / ≤35 / ≤45 turns).

- [ ] **Step 8 — Polish**
  - [ ] Full docstrings (PEP 257), type hints everywhere, `make lint-strict` clean.
  - [ ] Finish README: algorithm choices, complexity, visualization write-up, resources/AI-usage.
  - [ ] Clean up temporary debug prints in `main.py`.

- [ ] **Step 9 — Bonus (only after Steps 1–8 are solid and green)**
  - [ ] Confirm all provided maps meet or beat their reference targets.
  - [ ] Attempt the Challenger map ("Impossible Dream", 25 drones) — beat 45 turns.
  - [ ] Log the best turn count achieved per map in the README.

**Suggested first commit:** Steps 1–3 (models + parser green against `example.map`).

---

## 1. Understanding the problem

At its core, Fly-in is a **flow-over-time / scheduling** problem (the classic 42 "lem-in" reimagined with drones), with several twists that make it harder than the original:

| Feature | Effect on the algorithm |
|---|---|
| `normal` zone | entering costs **1 turn** |
| `restricted` zone | entering costs **2 turns**; drone sits on the connection for 1 turn, *must* arrive next turn (can't wait extra) |
| `priority` zone | costs 1 turn but should be **preferred** (soft bias, not a hard rule) |
| `blocked` zone | never entered / never traversed — prune it entirely |
| `max_drones=N` | a zone can hold up to **N** drones at once (default 1) |
| `max_link_capacity=N` | a connection can be traversed by up to **N** drones per turn (default 1) |
| start / end | **unlimited** capacity |

So compared to plain lem-in (unit-capacity, unit-cost, vertex-disjoint paths), we need to handle **weighted edges** (restricted) and **capacities on both nodes and edges**. That pushes the "correct" model from *disjoint paths* toward a **min-cost flow** with node splitting.

**The winning insight:** the number of turns is *not* just the shortest path length. It's the **makespan** of pipelining N drones across a chosen set of paths. Sometimes using one extra, slightly-longer path lowers total turns; sometimes it doesn't. The algorithm has to *choose how many paths to use* and *how to spread drones across them*.

### Open questions to confirm with peers (don't assume)
- **Connection name in output.** The format prints `D1-<connection>` while a drone is mid-transit toward a restricted zone, but connections in the map are only identified by their endpoints (`zone1-zone2`). Decide on a canonical connection id (e.g. `<from>-<to>`) and be consistent. Clarify during peer review.
- **Restricted cost & the start.** Confirm whether the 2-turn cost applies on the *edge into* the restricted zone (it does per the spec — "movement *to* this zone costs 2 turns").
- **"any number of drones"** — the parser must accept large counts; make sure nothing is hard-coded.

---

## 2. Target architecture (OOP)

Everything at the **root of the repo** (submission rule). Keep classes small and single-purpose so you can explain each one in review.

```
fly-in/
├── Makefile
├── README.md
├── .gitignore
├── main.py                 # entry point: parse → solve → simulate → visualize
├── models/
│   ├── zone.py             # Zone hierarchy (see below)
│   ├── connection.py       # Connection (edge + capacity)
│   ├── network.py          # Graph: zones + adjacency, lookups, neighbors
│   └── drone.py            # Drone: id, position, path, state (at_zone / in_transit)
├── parsing/
│   ├── parser.py           # File → Network + nb_drones, line-accurate errors
│   └── errors.py           # ParseError, InvalidMapError, NoPathError
├── pathfinding/
│   ├── pathfinder.py       # abstract PathFinder (Strategy pattern)
│   ├── bfs_flow.py         # baseline: BFS multi-path (edge-disjoint)
│   └── mincost_flow.py     # advanced: weighted min-cost flow + node splitting
├── simulation/
│   ├── scheduler.py        # assign drones to paths, pick best flow value
│   └── simulator.py        # turn-by-turn engine, enforces all capacity rules
├── visualization/
│   ├── visualizer.py       # abstract Visualizer
│   └── terminal.py         # colored terminal output
└── maps/                   # your own test maps + the provided ones
```

### Class design (this is where "completely object-oriented" is proven)

**Zone hierarchy** — you already know Strategy/Abstract-Factory patterns; use them here.
- `Zone` (abstract base): `name`, `x`, `y`, `color`, `max_drones`, `occupants`.
  - `entry_cost` → property/abstract method returning the turn cost.
  - `is_accessible` → bool.
  - `has_capacity()` → checks occupancy against `max_drones` (start/end override to always-True).
- Subclasses: `NormalZone` (cost 1), `RestrictedZone` (cost 2), `PriorityZone` (cost 1, preferred), `BlockedZone` (inaccessible). Start/end can be `StartZone`/`EndZone` with unlimited capacity, or a flag on the base.
- A small `ZoneFactory` maps the parsed `zone=<type>` string to the right subclass and raises on unknown types.

**Connection**: `zone_a`, `zone_b`, `max_link_capacity`, live traversal count per turn. Provides `other_end(zone)` and `can_traverse()`.

**Network (Graph)**: dict `name → Zone`, adjacency `name → list[Connection]`. Methods: `add_zone`, `add_connection` (rejects duplicates a-b == b-a), `neighbors(zone)`, `start`, `end`. **No graph libraries** (networkx/graphlib forbidden) — you implement BFS/Dijkstra/flow by hand.

**Drone**: `id`, `position` (a `Zone` or a `Connection` while in transit), `remaining_transit`, assigned `path`, `delivered` flag. A `step()` / state machine keeps the restricted 2-turn transit correct.

**Custom exceptions** in `parsing/errors.py` so failures are clean (spec: unhandled crash = non-functional).

---

## 3. Algorithm strategy (the heart of the project)

Build it in **two tiers** so you always have something working, and the second tier is what unlocks the hard maps + bonus.

### Tier 1 — Baseline (get easy + most medium maps green)
1. **Prune** blocked zones from the graph.
2. **BFS shortest path** start → end.
3. **Multi-path search** via BFS-based max flow (Edmonds-Karp style): repeatedly find augmenting paths in a residual graph until none remain. This gives a set of edge-disjoint paths respecting `max_link_capacity`.
4. **Distribute drones** across the found paths greedily to balance the makespan (assign each next drone to whichever path finishes earliest).
5. **Simulate** turn by turn (see §4) and count turns.

This is easy to explain in peer review and already hits many targets.

### Tier 2 — Advanced (hard maps + bonus + challenger)
Upgrade the two weak spots of Tier 1: it ignores restricted-zone *weights* and node *capacities > 1*.

1. **Node splitting for `max_drones`:** split each zone `v` into `v_in → v_out` with capacity `max_drones` (start/end get ∞). All incoming connections point to `v_in`, all outgoing leave from `v_out`. This is the standard trick to turn node capacity into edge capacity.
2. **Weighted edges:** put the entry cost on the split edge (1 for normal/priority, 2 for restricted). Give `priority` zones a tiny cost discount (e.g. 0.99, or a secondary tie-break key) so they're *preferred* without breaking correctness.
3. **Min-cost max-flow** by successive shortest augmenting paths. Use **Dijkstra with Johnson potentials** (not plain Bellman-Ford) so it stays fast on the 25-drone challenger map.
4. **Search the flow value:** for each feasible number of paths `f = 1 … maxflow`, decompose the flow, run the simulator, record the makespan. **Pick the `f` with the fewest turns.** The simulator is cheap, so this brute-force-over-f is affordable and reliably near-optimal.
5. Cache/reuse computed paths — don't recompute per turn (the subject explicitly asks "are you recalculating or caching paths?" — answer: caching).

**Complexity to state in the README:** BFS is `O(V+E)` per path; min-cost flow with potentials is roughly `O(F · E log V)` where `F` is total flow; the flow-value search multiplies simulation (cheap, `O(turns · drones)`) by `maxflow`. Memory is `O(V+E)` for the graph plus `O(drones)` for tracking.

---

## 4. The simulator (turn engine) — get the rules exactly right

This is where most points are lost. Process **one turn** as:

1. **Compute intended moves** for every non-delivered drone based on its assigned path.
2. **Free space first:** a zone a drone is *leaving* frees capacity *this same turn* (spec: "drones moving out free up capacity for that same turn").
3. **Validate against capacity** in the right order: a move into a zone is allowed only if, after all leavers are removed, there's room (`occupants < max_drones`), and the connection's `max_link_capacity` isn't exceeded this turn.
4. **Restricted transit:** dispatching a drone onto a restricted-bound connection commits it to arrive *next* turn — it **cannot** linger. So only dispatch when you can guarantee the destination will have capacity next turn. While in transit, output `D<id>-<connection>`.
5. **Resolve conflicts / deadlocks:** if two drones want the same last slot, pick deterministically (e.g. the one closer to the goal, or lower id) and make the other **wait**.
6. **Emit the turn line:** space-separated `D<id>-<zone>` (or `-<connection>`), omitting drones that didn't move.
7. Mark arrivals at `end` as delivered; stop when all delivered.

Keep the simulator **pure and deterministic** — same input → same output. That makes it testable and lets the scheduler try many flow values.

---

## 5. Parser & error handling

Must be strict (spec lists these explicitly):
- First line `nb_drones: <positive int>`.
- Exactly **one** `start_hub:` and **one** `end_hub:`.
- Unique zone names; integer coords; names may not contain dashes or spaces.
- Connections only reference already-defined zones; reject duplicates (`a-b` == `b-a`).
- Metadata blocks `[...]` syntactically valid; tags in any order; unknown `zone=` type → error.
- `max_drones` / `max_link_capacity` are positive integers.
- `#` comments ignored.
- **Any** parse error stops the program with a clear message giving **line number + cause**.

Use context managers for file handles, wrap parsing in try/except, and raise your custom `ParseError`. Build your **own edge-case maps** (missing start, duplicate connection, bad type, capacity 0, self-loop, disconnected end, huge nb_drones) — the subject strongly recommends this and reviewers will test it.

---

## 6. Visualization

Mandatory. Start simple, upgrade if time allows.
- **Terminal (do this first):** ANSI colors driven by each zone's `color` metadata; render the turn line, zone occupancy, and a small legend. Also print the **secondary metrics** (turns, drones/turn, avg turns/drone, total path cost) — the subject encourages showing these to help reviewers.
- **Graphical (optional polish):** a simple matplotlib/pygame view of zones at their `x,y` with drones animating along edges. Only after the mandatory part is fully green.
- Keep visualization **decoupled** from the simulator (an abstract `Visualizer` the simulator feeds events to) so it never affects correctness.

---

## 7. Tooling & compliance checklist

- **Python 3.10+**, PEP 257 docstrings, `typing` hints everywhere, passes `mypy` (and aim for `mypy --strict` → the optional `lint-strict` rule).
- **Makefile** rules: `install`, `run`, `debug` (pdb), `clean`, `lint` (flake8 + the exact mypy flags from the subject), `lint-strict` (optional).
- `.gitignore` for `__pycache__`, `.mypy_cache`, venv, etc.
- **venv** for dependency isolation during dev.
- **Tests** with pytest (not graded, but they'll save you): parser edge cases, simulator invariants (never exceed capacity, all drones eventually delivered), and turn-count regression on the provided maps.
- **README.md** (English) with: the exact required first italic line, `Description`, `Instructions`, `Resources` (incl. **how AI was used, for which tasks**), plus your **algorithm choices / strategy** and **visualization** write-up.

---

## 8. Phased roadmap (milestones → bonus)

| Phase | Deliverable | "Done" when |
|---|---|---|
| **0. Setup** | repo skeleton, Makefile, .gitignore, venv, mypy/flake8 config | `make lint` runs clean on empty skeleton |
| **1. Model + Parser** | Zone hierarchy, Connection, Network, Parser, custom errors, tests | all your bad-map cases raise clean line-accurate errors |
| **2. Single path** | BFS shortest path + minimal simulator, correct output format | linear map with 2 drones solves and prints valid turns |
| **3. Multi-path** | BFS max-flow + greedy distribution | easy + most medium maps hit their targets |
| **4. Full mechanics** | restricted 2-turn transit, node/link capacity, priority bias in simulator | capacity + restricted maps validate with zero rule violations |
| **5. Optimize** | node-split min-cost flow + flow-value search | **hard maps** meet targets (≤30/≤35/≤45) |
| **6. Visualization** | colored terminal + secondary metrics | reviewer can *see* the simulation clearly |
| **7. Polish** | docstrings, `mypy --strict`, README, cleanup | `make lint-strict` clean; README complete |
| **8. BONUS** | perfect targets on all maps + Challenger | "Impossible Dream" (25 drones) beats **45** turns |

**Bonus gate:** the bonus is only reviewed if the mandatory part is fully met — so don't touch Phase 8 until Phases 0–7 are solid and green.

---

## 9. Bonus strategy (Challenger — beating 45 turns)

- The flow-value search (§3, step 4) is what gets you *provably good* makespans across all provided maps → the "perfectly meet all targets" bonus.
- For the 25-drone challenger: speed matters, so keep the min-cost flow on **Dijkstra + potentials**, precompute and cache all paths once, and only re-run the cheap simulator across candidate flow values.
- Consider a light **local-search / balancing** pass over drone-to-path assignment (move a drone from the makespan-critical path to a slacker one and re-simulate) to shave the last few turns.
- Track the best turn count found and keep it; log it in the README as your result vs. the 45 reference.

---

## 10. Top risks / gotchas (where projects fail review)

1. **Restricted transit rule** — the "can't wait on the connection" constraint is easy to violate; guard dispatch by checking destination capacity for *next* turn.
2. **Capacity ordering per turn** — leavers must free space *before* enterers are validated, in the same turn.
3. **Duplicate connections** (`a-b` vs `b-a`) and **blocked-zone pruning** — handle at parse time.
4. **Priority as a soft preference**, not a hard constraint — don't accidentally forbid non-priority paths.
5. **Determinism** — non-deterministic tie-breaks make bugs unreproducible and reviews painful.
6. **mypy under `--strict`** — annotate generics (`dict[str, Zone]`, `list[Connection]`), avoid `Any`.
7. **"Explain / modify on the spot"** — the review may ask you to tweak behavior live. Because the design is modular (parser / graph / pathfinder / simulator / visualizer), a small change touches one class. Know each class well enough to edit it cold.

---

### Suggested first commit
Phase 0 + a stub `Zone`/`Network`/`Parser` that reads the example map from the subject and prints the parsed graph. Small, green, and it proves the skeleton compiles and lints. Build up from there.