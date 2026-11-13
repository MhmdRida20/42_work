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
| `maps/` | `example.map`, the official maps in `easy/`, `medium/`, `hard/`, `challenger/`, our own `easy_linear.map`, the `bad_*` maps (parse errors) and the `edge_*` maps (Step 6.10). |
| `tests/` | pytest suite. Not submitted (subject III.3), but it's how every step is verified. |

### `models/` — the domain objects (the "nouns" of the simulation)

| File | Contains |
|---|---|
| `zone.py` | `Zone` abstract base (`name`, `x`, `y`, `color`, `max_drones`, `unlimited`, `occupants`, abstract `entry_cost`, `is_accessible`, `has_capacity()`). Subclasses `NormalZone`, `RestrictedZone`, `PriorityZone`, `BlockedZone`. `ZoneFactory.build()` turns a parsed `zone=<type>` string into the right subclass (raises on unknown type). Start and end are not subclasses: they are zones with `unlimited=True`. |
| `connection.py` | `Connection`: an undirected edge (`zone_a`, `zone_b`, `max_link_capacity`, `in_transit` counter). `name` is the connection as written in the map (`zoneA-zoneB`), printed during restricted transit. `other_end(zone)` and `can_traverse()`. |
| `network.py` | `Network`: the graph — `zones: dict[str, Zone]`, `adjacency: dict[str, list[Connection]]`, `start`/`end` properties, `add_zone`, `add_connection` (rejects duplicates/self-loops), `neighbors(zone)`, `connection_between(a, b)`. No graph library — all traversal is hand-written elsewhere. |
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
| `bfs_flow.py` | `BFSFlowFinder` — the baseline strategy: one shortest path by number of connections, shared by all drones. It ignores turn costs, so it isn't the final planner; the simulator tests use it because one path makes their schedules easy to predict. |
| `space_time.py` | `ReservationTable` and `SpaceTimeFinder` — the real planner, used by `main.py`: one timed route per drone, found through (zone, turn) states. See §3. |

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
| `frames.py` | *(Step 7b)* `Pose`, `Frame`, `Recorder`: the run turned into data, one frame per turn. No pygame. |
| `layout.py` | *(Step 7b)* `Layout`: map coordinates to pixels, zone and drone sizes, slots, points on a link. No pygame. |
| `playback.py` | *(Step 7b)* `Playback`: the replay clock (turn, progress, speed, pause) and where each drone is at any moment. No pygame. |
| `graphical.py` | *(Step 7b)* pygame-ce: `SceneRenderer` (draws one moment), `GraphicalViewer` (window and event loop), `GraphicalVisualizer` (the `Visualizer` that records, then opens the window). |

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
  - [x] **5.7 Referee** in `tests/test_referee.py` (not the simulator's code): a `Referee` class replays the lines `main.py` printed and checks every rule on its own: adjacency, connection names as the map wrote them, blocked zones, zone capacity including the take-off reservation, link capacity including landing drones, a multi-turn move lasts exactly `entry_cost` turns, nobody waits on a connection, every drone is delivered. Run on every map, every time, with its turn count, plus hand-made bad runs that prove each check fires.
  - [x] **5.8 `make test`:** it failed with collection errors, because bare `pytest` puts `tests/` on the import path but not the project, so `import models` fails. The rule is now `$(PYTHON) -m pytest -q`. On Windows the venv has no `python3`, so run `make test PYTHON=.venv/Scripts/python.exe`. The Makefile comment's example is now `maps/easy/01_linear_path.txt` (`maps/easy_2.map` never existed).
  - [x] Verify: flake8, mypy, tests and referee clean. Turn counts match the "BFS + transit" column in §3, including `03_priority_puzzle` at 13 turns, which misses its target of 12 until Step 6.

- [x] **Step 6 — Space-time planner** (`pathfinding/space_time.py`, see §3)
  Replaces both the old BFS multi-path task and the old min-cost flow step. The core (6.1–6.7) is what meets every target and the Challenger; 6.8 and 6.9 are hardening. Done 2026-11-02; its output is identical to the lab prototype's on all 10 official maps, our own maps and 2000 random maps.
  - [x] **6.1 `Network.connection_between(a, b)`:** moved here from `Simulator._connection_between`, because the planner needs it too.
  - [x] **6.2 Planned waits:** a repeated zone in a path means "stay one turn". `step()` sorts ready drones into `movers` and `waiters`; a waiter calls `advance()`, keeps its place in `occupants`, uses no connection and prints nothing.
  - [x] **6.3 `Scheduler.assign`:** gives each drone `paths[index % len(paths)]`, so one shared BFS path and one route per drone both work.
  - [x] **6.4 `ReservationTable`:** who holds which zone and link on which turn. `zone_is_free`, `can_move` (checks every turn of the movement, so 2-turn moves need no special case), `book_route`. Unit-tested alone, including opposite directions sharing a link.
  - [x] **6.5 `SpaceTimeFinder(nb_drones)`:** for each drone, search (zone, turn) states for the earliest arrival. It's your BFS with time added to the state: `parents` and the rebuild are the same idea. `_moves` lists the legal next steps of a state (waiting, if the zone has room, and every move the table allows). A restricted move jumps 2 turns, so the queue is a `heapq`. Book the route, then plan the next drone. `nb_drones` goes to the constructor, so `PathFinder.find_paths(network)` keeps its signature.
  - [x] **6.6 Tie-break:** among equal arrival turns, the least effort wins: priority zone 1, any other zone 2, waiting 0. A bonus for priority zones doesn't work: a drone bounces in and out of them to collect it. Tested on `edge_priority_tie.map`, where the normal zone comes first by name.
  - [x] **6.7 Wired into `main.py`.** The referee test checks every map against the "Space-time" column in §3. `example.map` went from 12 turns to 6, with the drones using both routes.
  - [x] **6.8 Second pass:** plan everything once, count how many drones entered each zone, plan again with "avoid crowded zones" as the first tie-break, and keep the better plan (the first one on a tie). No official map needs it (both passes give the same count on all 10), so `edge_crowded_tie.map` (random seed 1138) tests it: 25 turns with one pass, 15 with two, and 15 is the proven best.
  - [x] **6.9 Speed for large drone counts:** each zone's distance to the end is computed once, backwards from the end. A zone missing from it is blocked, or linked to the rest only through blocked zones. In an undirected map a dead end still has a distance (go back the way you came), so this replaces the reachability check rather than pruning dead ends. The heap is ordered by `turn + distance`. Each drone's search starts at `last arrival - window`, with `window = 2 * distance from start + number of zones`. Measured in §3.
  - [x] **6.10 Edge-case maps** next to the bad ones, each with its expected turn count worked out by hand in its comment: `edge_start_to_end` (3), `edge_restricted_end` (5), `edge_two_restricted` (7), `edge_priority_tie` (2), `edge_crowded_tie` (15), `edge_1000_drones` (501, about 2 s), `edge_no_path_disconnected` and `edge_no_path_blocked` (clean "no path" error). Drones using one link in opposite directions is a `ReservationTable` unit test: the planner never routes two drones against each other, so no map can force it.
  - [x] **6.11 Clean up:** `mincost_flow.py` deleted, with its import in `tests/test_smoke.py`. Docstrings in `bfs_flow.py`, `pathfinder.py`, `scheduler.py` and the `Simulator` corrected.
  - [x] Verify: 117 tests, flake8 and mypy (`--strict` too) clean. Referee clean on every map and on 1331 solvable random maps. Same output under 4 different `PYTHONHASHSEED` values. Every drone arrives on the exact turn its route promised (a test). 20 deliberate bugs: 18 caught, and the 2 that survive can't change any output (the dead-end check, which matches blocked zones only; the window, which only saves time).

- [x] **Step 7 — Visualization** (mandatory, VII.1; see §6). Done 2026-11-02.
  - [x] **7.1 `show_network`:** every zone in its map color with its role, type, capacity and entry cost; blocked zones marked "never entered"; connections with their capacity; a short "how to read a turn".
  - [x] **7.2 `show_turn` with zone states:** takes a `network` parameter now. After the exact movement line it prints one state line: drones waiting in the start, each busy zone as `used/max: D…`, each drone flying toward a restricted zone (`D3 to roof1 via hub-roof1`), and `delivered/total` at the end. `occupants` also holds drones still flying toward a zone, so "inside" compares `drone.position is zone`.
  - [x] **7.3 Hook:** `Simulator.run(visualizer=None)` calls `show_turn` after each turn. Existing calls to `run()` work unchanged.
  - [x] **7.4 `show_summary`:** `Simulator.metrics()` gives turns, drones moved per turn (movement tokens / turns, so a flying drone counts on both turns), average turns per drone (from `Drone.arrival_turn`, set in `run()`), and total path cost (`path_cost` now skips waits).
  - [x] **7.5 Colors:** the maps use 18 names (17 plus `gray` in `example.map`); all are 256-color codes now. `black` is black on a light background, `rainbow` colors each letter in turn, names ignore case, unknown names stay plain.
  - [x] **7.6 Keep the format exact:** the `D<id>-…` lines are printed untouched. `main.py` uses the visualizer only when `sys.stdout.isatty()`; piped or redirected, it prints only the movement lines.
  - [x] Verify: 130 tests, flake8 and mypy (`--strict` too) clean. Piped output is unchanged and the referee accepts it. A test fakes a terminal and checks the movement lines are still exact. 12 deliberate bugs in the Step 7 code, all caught. Still to do by eye: watch a colored run in a real terminal (§11 review checklist).

- [ ] **Step 7b — Graphical view with pygame-ce** (VII.1 allows terminal *or* graphical and suggests both; full design in §6.2)
  The terminal view stays the default. `--visual` adds a window that **replays** the run once it is computed: the planner and the simulator don't change, and the printed lines stay exact. Each sub-step ends with tests; 7b.2 to 7b.4 import no pygame at all.
  - [x] **7b.1 Dependency:** add `pygame-ce` to `requirements.txt` and `make install` it (why not `pygame` or `arcade`: §6.2). In the venv, confirm what the scratch test of 2026-11-08 showed: `import pygame` prints a banner **to stdout** unless `PYGAME_HIDE_SUPPORT_PROMPT=1` is set before the import; `SDL_VIDEODRIVER=dummy` draws with no window; `make lint-strict` stays clean.
  - [x] **7b.2 Recording, `visualization/frames.py`:** `Pose`, `Frame`, and `Recorder(Visualizer)`, a visualizer that draws nothing: `show_network` records turn 0, `show_turn` records each turn, `show_summary` keeps the metrics (§6.2 "What a frame holds"). Test every frame of `edge_restricted_end.map` exactly, including D1 halfway along `a-e` on turn 2 and the link loads. Test that a restricted cost of 3 gives progress ⅓ then ⅔ (with cost 2 a backwards progress also gives ½, so only this test catches it).
  - [x] **7b.3 Layout, `visualization/layout.py`:** `Layout(network, width, height)`, built again when the window is resized; a window under 800 × 560 is laid out at that size. Map coordinates to pixels (y up, each axis fitted on its own, a one-value axis centred), zone and drone radius, `slot(zone, rank)` (the start, the end and one-drone zones use the centre), `on_link(link, toward, progress)` (measured from the other end, found with `Connection.other_end`), two zones on the same coordinates. Tests with negative coordinates, a one-row map, the Challenger's 23 × 4 grid, the radius bounds, a resize and the minimum size.
  - [x] **7b.4 Replay clock, `visualization/playback.py`:** `Playback(frames)`. One number, `time`, counts turns (2.5 = two turns over, the third half done): `turn = ceil(time)` is the turn on screen, `progress` the share of it done, and `settled = frames[floor(time)]` the frame the counters come from. `update(ms)`, `toggle` (at the end it restarts), `restart`, `seek`, `next_turn`/`previous_turn` (pause on the frame after/before the screen), `faster`/`slower`, and `positions(layout)`: each drone's pixel at this moment (§6.2 "One turn on screen"). Tests: the easing, pause, both ends, steps from mid-turn, a drone leaving the start, a delivery, a 2-turn flight stopping halfway, slots by id. Written by Claude at your request on 2026-11-09 ("apply them"), so it is item 12 of the §11 review list.
  - [x] **7b.5 Drawing the map, `SceneRenderer` in `visualization/graphical.py`:** links (thicker with capacity; a used one glows, with `load/cap` beside its middle), zones (map color, the outline and badge of their type, a hole per place, a ring for a place reserved by a drone flying in, the name and `used/max` under it), the start and end counters, drones (id on the disc, dimmed after a wait, ringed in flight). The public `count_text`, `name_label`, `badge`, `zone_color` and `drone_color` decide what is shown; the private `_draw_*` methods paint it. Also in `layout.py`: the minimum drone radius goes from 5 to 7 px, so that an id fits on its disc (at 5 px the screenshots showed unreadable ids). Tests: importing prints nothing; every moment of every map draws, and before the first turn each zone's centre shows its fill; colors, badges, the type marks without color, the glow and its label, the flight ring, dimming, reserved places, counts, cut names, names off. Written by Claude at your request on 2026-11-09 ("apply them"), so it is item 13 of the §11 review list.
  - [x] **7b.5b Around the map:** the top bar (map name · `Turn k / T` · playing, paused or done · speed), the bottom bar (the movement line of the turn on screen, key hints), the legend (`L`), the tooltip on hover, the end-of-run summary with the metrics (§6.2 "What the screen shows"). `SceneRenderer(network, title, metrics)` and `draw(..., mouse=None)`. The public `bar_texts`, `zone_lines`, `drone_lines`, `tooltip` and `summary_lines` decide the texts; `_draw_bars` and `_draw_panel` paint them. The legend sits bottom-right: counted on every map, that corner covers the fewest zones (1 at 1280 × 800, against 4 bottom-left). The summary is a panel at the top centre, on the last turn only; the tooltip is 16 px from the mouse and kept inside the window. `_fit` now keeps its cut texts, because cutting the Challenger's 417-character line takes 18 ms. Tests: the bar texts, a long line cut, the zone, blocked-zone and drone tooltips, what is under the mouse (the drone drawn on top wins), the summary, the bars, the panels only when they should be, the tooltip moved inside the window; the every-map test now also draws the legend, a tooltip and the summary.
  - [x] **7b.6 Window, `GraphicalViewer`:** open the window, a 60 fps loop, keys and mouse (§6.2 "Controls"), resize, `pygame.quit()` in a `finally`. A missing pygame-ce or a `pygame.error` (no display) becomes `VisualizationError(FlyInError)`, so `main()` prints one clean line. Test the loop headless with posted events. Decided while writing it: `GraphicalViewer(network, frames, title, metrics)` with `run()`, `handle(event)`, `press(key)` (one `if`/`elif` per row of the Controls table), `resize(width, height)` and the static `_open()` and `_mouse()`. `_open()` starts only the display (`pygame.init()` would also start the sound, never used); the loop is tick, events, `update`, draw, flip. A window made smaller than 800 × 560 is set back with `set_mode`, which resizes the same window surface (checked with both libraries). The mouse counts only while over the window (`mouse.get_focused()`). `VisualizationError` joins the other errors in `parsing/errors.py`; `import pygame` sits in a `try` that turns an `ImportError` into it (an indented import needs no `# noqa: E402`). Tests: `tests/test_viewer.py`, 11 of them, with SDL's `dummy` driver, posted events and a stand-in clock that makes each picture a turn later. Under `dummy`, pygame-ce says the mouse is over the window and plain pygame says it isn't, so the mouse test fixes both answers. Every loop test ends with a QUIT, so a broken key fails a test instead of hanging it. 14 deliberate breaks, all caught.
  - [x] **7b.7 Hook:** `GraphicalVisualizer(Recorder)`: it inherits the recording and only overrides `show_summary` to keep the metrics, then open the window. Add `VisualizerGroup(Visualizer)` to `visualizer.py`: it forwards every call to several visualizers (the Composite pattern), so the terminal view and the window can run together. Decided while writing it: `GraphicalVisualizer(network, title)`. The window needs the network for its layout, and `main.py` has it right after parsing, so it comes with the constructor. `show_summary` keeps the metrics through `super()`, then runs a `GraphicalViewer` and returns when the window is closed. `VisualizerGroup(visualizers)` calls them in list order, so the terminal's summary is printed before the window opens and waits. Tests: `tests/test_visualizer.py` (the order of the calls; a group of two Recorders records what one records alone) and one more in `tests/test_viewer.py` (with `GraphicalViewer.run` replaced: the window opens only at the summary, with the recorded frames, the title and the metrics). 7 deliberate breaks, all caught.
  - [x] **7b.8 `main.py`:** `argparse` for `main.py MAP [--visual]` (`--help` for free; a missing map exits with code 2 and the usage, never a traceback). Import `visualization.graphical` only when `--visual` is given, so a normal run never loads pygame. With `--visual` and piped output: the plain lines first, then the window. `main()` grows here, so decide 8.4c (wrap it in a class) at this point. Decided 2026-11-11: 8.4c answered "keep one `main()`". The usage reads `python main.py [-h] [--visual] map_file` (`prog="python main.py"`). `main()` builds a list of visualizers: the terminal view on a terminal, then the `GraphicalVisualizer` with `--visual`. A `VisualizerGroup` of them always follows the run, even an empty one (piped, no `--visual`), so the `None` checks are gone. Piped, the lines are printed and `sys.stdout.flush()` sends them before the window opens. A missing pygame fails at the import, before the run, so nothing but the error line is printed. No screen fails when the window opens, after the lines: one `error:` line, exit 1. Tests in `tests/test_main.py` (12, 9 of them new): the usage, a mistyped option, `--help`, the lines before the window (piped and on a terminal), a real window under the `dummy` driver, no screen, no pygame for a plain run and for `--visual`, and the flush (a child Python replaces the window with `os._exit`, which skips the final flush). 7 deliberate breaks, all caught.
  - [x] **7b.9 Makefile:** a `visual` rule, `$(PYTHON) main.py $(MAP) --visual`. Done 2026-11-13: the rule, `visual` in `.PHONY`, and the comment above `MAP` names it. Checked with `make -n` (and the `MAP=`/`PYTHON=` overrides) and with no usable screen on both Pythons: the lines, then one `error:` line. Left to do by hand: watch the example, a restricted map, the Challenger and the 1000-drone map in a real window.
  - [ ] Verify: flake8, `mypy --strict`, all tests (headless). Every map replays to its last turn with the right turn count. `python main.py <map> --visual | cat` prints exactly the lines of a normal run. No pygame-ce, or no display: one `error:` line, exit 1. Watched by you on the example, a restricted map, the Challenger and the 1000-drone map.

- [ ] **Step 8 — Polish & defense**
  Requirements audit against the whole subject, 2026-11-03: everything in III, V, VI, VII and IX is implemented and checked. What is left is listed here (8.4b, 8.6, 8.9 are new), plus the README in Step 9.
  - [x] **8.1 README, do now:** add the final period to the first line (the PDF sets it in italics, so it is part of the required line), and correct the AI usage section: AI wrote the first version of Steps 1–4.
  - [x] **8.3** Full docstrings (PEP 257), type hints everywhere, `make lint-strict` clean. Checked 2026-11-03: an AST scan finds a docstring on every module, class and function, and `mypy --strict` is clean.
  - [x] **8.4 Small cleanups:** `NotImplementedError` is gone from the `except` in `main.py` (no stubs left), no `# TODO` comments remain, the `[mypy-numpy]` sections are gone from `setup.cfg` (lint still clean), and `make install` runs `$(PYTHON) -m pip`, so `pip` can't belong to another Python.
  - [x] **8.4b Two crash paths in `main.py` (III.1: a traceback counts as non-functional):** Ctrl+C now prints `interrupted` and exits with 130. When the reader of the output stops early (`| head`), `main()` points stdout at the null device (the recipe from Python's `signal` docs) and exits with 1, silently. The broken pipe was reproduced for real, on Windows too: a 200 KB line and a reader that closes after 20 bytes gave a `BrokenPipeError` traceback before, and an empty stderr after. Tests in `tests/test_main.py`.
  - [x] **8.4c (optional) "Completely object-oriented":** `main()` in `main.py` is the only function outside a class. An entry function is normally accepted; if a peer says otherwise, wrap it in a small class. Decided 2026-11-11, at 7b.8: keep one `main()` (about 50 lines, one `try`); wrapping it later stays possible.
  - [x] **8.5 Integer parsing:** `Parser._strict_int` accepts only an optional `-` followed by the digits 0-9, for `nb_drones`, capacities and coordinates. `1_0`, `+3`, `3.0` and Arabic digits are rejected with the line number; negative coordinates still work.
  - [x] **8.5b UTF-8 BOM:** fixed with `encoding="utf-8-sig"` (tested). The original finding: a map saved with a byte-order mark (Windows PowerShell 5.1's `Set-Content -Encoding utf8`, old Notepad) fails with `line 1: invalid line syntax: '﻿'`. Found 2026-11-02. Opening with `encoding="utf-8-sig"` accepts it and still reads plain UTF-8.
  - [ ] **8.6 Submission repo:** `Makefile`, `main.py` and `README.md` at the root of the repo you submit (today the git root is `42_work_git`, with the project in a subfolder). Leave out `tests/`, `plan_structure.md` and `subject_flyin.pdf`. Removing `tests/` also means removing the `test` rule and `pytest` from `requirements.txt`. Ask a peer whether `models/` and the other code folders are fine under "place all your files at the root".
  - [ ] **8.7 Fresh clone on a 42 machine:** `make install`, `lint`, `lint-strict`, `run`, `debug`, `clean`, and `make test`. The venv here is Python 3.14; the code compiles with the 3.10 grammar and gives the same output under 3.11, but Python 3.10 itself was never run.
  - [ ] **8.8 Defense rehearsal** (§11), without notes.
  - [ ] **8.9 (optional) Large drone counts:** it works, but time grows about with the square of the drone count, because each waiting turn is a route entry. Measured on the two-route map: 1000 drones 1.7 s, 3000 drones 17 s (planning 4.9 s, of which `book_route` 4.4 s; simulation 12 s), 5000 drones 50 s. Cheap: `book_route` can skip waits in unlimited zones (they never limit anyone). The real fix, a departure turn instead of leading waits, changes the route format the simulator and scheduler use: decide before starting.

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
│   ├── visualizer.py       # abstract Visualizer, VisualizerGroup (7b)
│   ├── terminal.py         # colored terminal output
│   ├── frames.py           # the run as data: Pose, Frame, Recorder (7b)
│   ├── layout.py           # map coordinates to pixels (7b)
│   ├── playback.py         # replay clock and drone positions (7b)
│   └── graphical.py        # pygame-ce window: renderer, viewer (7b)
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
3. **Goal direction and window (6.9).** Order the heap by `turn + distance to end`, skip zones that can't reach the end, and don't search departure turns too early to matter. Waiting at the start is always legal, so any plan this produces is still valid. The official maps' output didn't change.

### How sure are we?

The project's planner (Step 6) gives exactly the prototype's output on the 10 official maps, our own maps and 2000 random maps, so the prototype's measurements below hold for it. The timings were measured again on the project code, 2026-11-02.

- **Official maps:** all 10 optimal, each planned in under 0.1 s.
- **1331 solvable random maps, compared with the exact optimum:** 0 invalid schedules, 0 stuck runs, exact on 1327 (99.7%), never more than 1 turn off. Planning is a heuristic, not a proof: don't claim it is always optimal.
- **Planner and simulator agree:** every drone arrives on the exact turn its route promised, so no planned move is ever blocked (`test_every_drone_arrives_when_planned`).
- **Size:** about 150 lines of code for the planner, without docstrings.

| Drones | Hardest map (ultimate) | Narrow map (Challenger) |
|---:|---:|---:|
| 100 | 3.7 s | 0.3 s |
| 300 | 12 s | 0.9 s |
| 1000 | 53 s (48 s of it planning) | 5.0 s |

The prototype measured about half these times on 2026-10-31, with identical output. The difference is the machine, not the code. Planning (two passes) is almost all of it; simulation is about 2 s at 1000 drones.

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
- **Terminal (done, Step 7):** ANSI colors driven by each zone's `color` metadata; render the turn line, zone occupancy, drones in flight, and a small legend. Also print the **secondary metrics** (turns, drones/turn, avg turns/drone, total path cost) — the subject encourages showing these to help reviewers.
- **Graphical (Step 7b):** a pygame-ce window that replays the run on the map. Designed in §6.2.
- Keep visualization **decoupled** from the simulator (an abstract `Visualizer` the simulator feeds events to) so it never affects correctness. The required `D<id>-…` lines must stay exact; colors and states are additional, and disappear when the output is piped.

### 6.2 Graphical view (Step 7b)

**Library: pygame-ce.** Checked on 2026-11-08 in a scratch venv, so these are facts, not guesses:

| | pygame-ce 2.5.8 | pygame 2.6.1 | arcade 3.3.3 |
|---|---|---|---|
| Installs in your venv (Python 3.14, Windows) | yes | **no**: no 3.14 build, pip would try to compile SDL | yes |
| Installs on a 42 machine (Python 3.10, Linux) | yes | yes | yes |
| API | pygame's (`import pygame`): what you already know | pygame | new to you |
| Needs | any display; can draw with no window, for tests | same | OpenGL 3.3 (fails on many VMs and remote sessions), plus pyglet, pymunk, Pillow |
| `mypy --strict` and flake8 on a game-loop sample | clean | not tested | not tested |
| Map color names it knows | 17 of 18 (not `rainbow`) | same names | own palette |

pygame-ce is the community edition of pygame, with the same import name, so the two can't both be installed in one venv. Drawing 1000 drone discs and 80 text labels took 3.1 ms per frame headless (60 fps allows 16.7). The code uses only what both libraries have: `Color.from_hsva` (pygame-ce only) broke `make test` under plain pygame 2.5.2 on 2026-11-10 and was replaced by the `hsva` property; since then every test passes with both pygame-ce 2.5.8 (Python 3.14) and plain pygame 2.5.2 (Python 3.11). On Windows, plain `make test` runs `python3`, the Microsoft Store Python 3.11 with plain pygame, because a Windows venv has no `python3.exe`: use `make test PYTHON=.venv/Scripts/python.exe` for the venv.

**The banner rule.** `import pygame` prints `pygame-ce 2.5.8 (SDL 2.32.10, Python 3.14.6)` **to stdout**, which would break the output format. With `PYGAME_HIDE_SUPPORT_PROMPT=1` set before the import, it prints nothing (both checked). So `graphical.py` sets `os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")` right before `import pygame`, which needs one `# noqa: E402` with a comment saying why. A test imports the module in a subprocess and checks that stdout is empty.

**How it runs: record, then replay.**

```
python main.py MAP --visual
  parse -> plan -> Simulator.run(VisualizerGroup([terminal view if a terminal, GraphicalVisualizer]))
      show_network(network)          -> Recorder: frame 0 (everyone in the start)
      show_turn(k, line, network)    -> Recorder: frame k (pure data, no pygame)
  piped: the plain lines are printed, exactly as without --visual
  show_summary(metrics)              -> terminal summary, then the window replays frames 0..T
  window closed                      -> exit 0
```

Why a replay and not a live view:
- The simulator stays exactly as it is. A window needs its own event loop, and a live view would make the run wait for the screen, or freeze the window between turns.
- A replay can pause, step back, restart and change speed, which a live run can't.
- The result is never lost: the lines are printed before the window opens, and closing the window early changes nothing.
- Recording is plain data, so it can be tested without a screen.

**What a frame holds** (`frames.py`, frozen dataclasses):

- `Pose(zone: str, link: str | None, progress: float)`: inside a zone, `link` is `None` and `progress` is 1.0. Flying, `zone` is the destination, `link` the connection's map name, and `progress` the share of the flight done: `(entry_cost - remaining_transit) / entry_cost`. That's ½ after a restricted take-off, and ⅓ then ⅔ if restricted ever costs 3.
- `Frame(turn: int, line: str, poses: dict[int, Pose], waiting: int, delivered: int, link_load: dict[str, int])`.

Recording rules, `Recorder.capture(network, turn, line)`:
1. For every zone, each occupant is **inside** if `drone.position is zone`; otherwise it is **flying toward** this zone, on the connection `drone.position` (`occupants` holds the reservation).
2. A drone gets a `Pose` if it is between the start and the end, **or** if it moved this turn (its location differs from the previous frame; the recorder keeps each drone's last location). Drones resting in the start or the end are only counted, in `waiting` and `delivered`. A frame therefore holds few poses: at most 18 drones are in play at once on the Challenger, and 2 on the 1000-drone map.
3. `link_load` is each connection's `in_transit` after the turn, when above 0. The simulator already counts movers and flying drones there.
4. Frame 0 has no poses, an empty line, and every drone waiting.

**One turn on screen** (`playback.py`). Turn k is an animation from frame k-1 to frame k, lasting 600 ms at ×1, with smoothstep easing `t * t * (3 - 2t)`:

| Drone in frame k-1 | Drone in frame k | During turn k |
|---|---|---|
| no pose (waiting in the start) | pose | from the start's centre to its new place |
| pose | pose | straight from its old place to its new place |
| pose (just reached the start or the end) | no pose | already there: now part of that zone's counter |

A pose's **place** depends on where the drone is:
- inside a normal zone: its slot (rank by id among the drones inside that zone in that frame);
- in the start or the end: the zone's centre;
- flying: the point at `progress` along the link, measured from the other end toward `zone`.

So a restricted move is **two** animations: from the slot to the middle of the link on the take-off turn, then from the middle to the destination slot on the landing turn. When paused in between, the drone sits on the link with a ring around it. Each 2-turn flight therefore shows the rule "it can't wait on the connection": with cost 2, a drone is never on a link in two frames in a row.

During turn k, the links in `link_load` glow and show `load/capacity`. Counters, slots and `used/max` switch to frame k when the animation ends, so what you see while paused is exactly the state after that turn.

**What the screen shows** (`graphical.py`; 1280 × 800 by default, resizable, minimum 800 × 560):

- Top bar: map name · `Turn k / T` · playing or paused · speed.
- Map area: links under zones under drones.
- Bottom bar: the movement line of turn k, exactly as `main.py` prints it, and the key hints.
- Legend (toggle `L`, off at first): zone types, marks, drone states, in the bottom-right corner.
- End overlay, on the last turn: the four metrics from `Simulator.metrics()`.
- Tooltip on hover: a zone's name, type, capacity and drones; a drone's id and location.

| Thing | Drawn as |
|---|---|
| zone | filled circle in its map color (`pygame.Color(name)`; an unknown name gives gray; `rainbow` cycles its hue over time); black zones get a light outline |
| normal / priority / restricted / blocked | plain / double outline and a `P` badge / dashed outline and a `2` badge (turns to enter) / dark gray, crossed out, no slots. The type never depends on color alone. |
| start / end | bigger circle, `S` / `E` badge, counter `12 waiting` / `5/25 delivered` |
| capacity | a hole for each place, up to 8 on a ring (a zone for one drone has none: its drone sits at the centre), and a white ring for a place reserved by a drone flying in; `used/max` under the name. A zone holding more than 8 shows 8 holes, and `used/max` gives the rest: no map has one, apart from the start and the end. |
| link | gray line, thicker with capacity; glows and shows `load/cap` during a turn that uses it |
| drone | small disc with its id written on a box of its color (a long id makes a pill), one hue per id (golden-ratio steps, so neighbours differ) |
| drone flying | the same disc with a white ring, on the link |
| drone that waited this turn | dimmed |
| zone names | small font under the circle, cut with `…` when longer than the space to the next zone; full name in the tooltip; `N` toggles them |

**Layout math** (`layout.py`, recomputed when the window is resized):
- Map area = the window minus the two bars (40 px at the top, 60 px at the bottom) and a 60 px margin.
- Each axis is fitted on its own: `sx = width / (max_x - min_x)` and `sy = height / (max_y - min_y)`, each capped at 160 px per unit, and an axis with one value is centred. Coordinates are grid positions, not distances: with one shared scale, the Challenger (23 wide, 4 tall) would be a thin strip.
- **y points up**: `screen_y = top + (max_y - y) * sy`. The subject's figures draw `path_a` (y = 1) above `path_b` (y = -1).
- Zone radius `clamp(0.28 * min(sx, sy), 10, 26)`, drone radius `max(7, zone_radius // 3)`: under 7 px an id doesn't fit on its disc.
- Slots: capacity 1 in the centre; up to 8 on a ring of 0.55 × the zone radius.
- A point on a link: `a + (b - a) * progress`.
- Two zones on the same coordinates (the parser accepts it): the second is shifted by one radius, so both stay visible.

**Controls:**

| Key | Action |
|---|---|
| Space | play / pause (it starts playing at ×1) |
| → / ← | next / previous turn (pauses) |
| ↑ / ↓ | faster / slower, ×0.25 to ×8 |
| Home / End | first / last turn |
| R | restart from turn 0 |
| N / L | zone names / legend on or off |
| Esc, Q, closing the window | quit |
| mouse over a zone or a drone | tooltip |

**Speed and memory.** Frames hold only the drones in play. The whole map is drawn again for every picture: measured on 2026-11-09, the Challenger (54 zones) takes about 2.5 ms, against 16.7 ms per picture at 60 fps, so the "static part drawn once per window size" first planned here was dropped. Text surfaces are cached by (text, size, ink, box), because rendering text is the slow part. Never-reached rules were dropped too: "ids hidden over 40 drones in play" (the most any map has is 18) and "+n over 8 places" (only the start and the end hold more than 8, and they show counters).

**Errors.** No pygame-ce: `VisualizationError("the graphical view needs pygame-ce: run make install")`. No display: `pygame.error` becomes `VisualizationError("cannot open a window: …")`. Both inherit `FlyInError`, so `main()` prints one `error:` line and exits with 1, after the lines are already printed. Ctrl+C while the window is open: `pygame.quit()` runs in the `finally`, then the existing handler exits with 130.

**Tests without a screen.** `frames.py`, `layout.py` and `playback.py` import no pygame, so they are plain unit tests. The renderer draws on a plain `pygame.Surface`, which needs no window: its tests import pygame like any requirement and read pixels. The window's tests (7b.6) use `SDL_VIDEODRIVER=dummy` and drive the loop with posted events. `make lint-strict` needs pygame-ce installed, because `--strict` has no `--ignore-missing-imports`; `make install` covers that.

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
| **7b. Graphical view** | pygame-ce window replaying the run (`--visual`) | every map replays; printed lines unchanged; headless tests green |
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
10. **pygame's banner on stdout** — `import pygame` prints a line to stdout unless `PYGAME_HIDE_SUPPORT_PROMPT=1` is set first, which would break the output format (§6.2).
11. **No display, or no pygame-ce, on the evaluation machine** — `--visual` must fail with one clean line, and a normal run must never import pygame, so the terminal view always works.
12. **pygame and pygame-ce share the import name** — if plain `pygame` is installed in the same Python, one breaks the other. The venv keeps them apart; `requirements.txt` names only `pygame-ce`.

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
| How does your visual representation enhance understanding? | Zone states and drones in flight show *why* a drone waits, which the movement lines alone can't show. In the window (7b): the 2-turn flight stopping halfway along the link, the hollow slot reserved in its destination, the links used each turn with `load/cap`, and a drone dimmed while it waits for a full zone. Pause and step through the turns to show it. |
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
- In the window (7b): change the turn duration or the default speed, color drones by state instead of by id, show the turn number on the map, add a key that hides blocked zones.

### Review of the code Claude wrote (5.7 to Step 8, then 7b.4 to 7b.8)

Work top to bottom. For each item: read it, explain it out loud, then do the "try" (a deliberate break; the named test must fail), and undo it with `git restore <file>`. Every "try" was checked: it fails exactly that test. Line numbers are from 2026-11-02.

- [ ] **0. Commit first**, so `git restore` brings back the verified version. Then `git diff 740c457 --stat` lists every changed file, and `git diff 740c457 -- <file>` shows one.
- [ ] **1. Watch it run** in the VS Code terminal: `.\.venv\Scripts\python.exe main.py maps/example.map` (colors, zone states, summary), then the Challenger map (black, rainbow, 43 turns). Then `... main.py maps/example.map > out.txt` and open `out.txt`: only the 6 movement lines.
- [ ] **2. Models:** `Drone.arrival_turn` (`drone.py:38`), `Network.connection_between` (`network.py:110`, moved from the simulator).
- [ ] **3. Simulator:** `movers`/`waiters` (`simulator.py:109`): a repeated zone is a wait, the drone advances, keeps its place and prints nothing. `run(visualizer)` (`:40`) sets `arrival_turn` and calls `show_turn`. `metrics()` (`:65`). Try: delete the `for drone in waiters` loop → `test_every_map_breaks_no_rule[maps/example.map-6]`.
- [ ] **4. Scheduler:** `paths[index % len(paths)]` (`scheduler.py:47`), `path_cost` skips waits (`:52`). Try: remove `if there is not here` → `test_path_cost_skips_planned_waits`.
- [ ] **5a. `ReservationTable`** (`space_time.py:31`): two counters keyed by (name, turn). `zone_is_free`, `can_move` (every turn of the move), `book_route` (a wait books the zone; a move books the link and the destination on each of its turns). Try: in `can_move`, `range(turn, turn + 1)` → `test_can_move_needs_the_zone_on_every_turn_of_the_flight`.
- [ ] **5b. `find_paths`** (`:102`): distances, the "no path" check, two passes, keep the better. Try: `return first` → `test_every_map_breaks_no_rule[maps/edge_crowded_tie.map-15]` (25 turns).
- [ ] **5c. `_plan_all`** (`:131`): drones in id order, the window and `earliest`.
- [ ] **5d. `_earliest_route`** (`:163`): the heap tuple order (best arrival, crowding, effort, turn, name, parent); `parents` is your BFS's visited set and parent map; the first end state popped is the earliest arrival; `earliest` waits at the start are added in front.
- [ ] **5e. `_moves`** (`:224`): waiting (only if the zone has room, effort 0) and every move `can_move` allows (effort 1 priority, 2 other). The one place the code differs from the lab prototype: pulled out of the loop so the "waiting needs room" rule could be tested; output identical on 2012 maps. Try: waiting effort 1 → `test_waiting_needs_room_and_costs_no_effort`; priority effort 2 → `test_priority_route_wins_a_tie`.
- [ ] **5f. `_distances_to_end`** (`:261`, Dijkstra backwards from the end; a missing zone is blocked) and `_rebuild` (`:292`).
- [ ] **6. `main.py:33`:** the visualizer only on a terminal. Try: swap the two branches → the referee tests fail (piped output gets extra lines).
- [ ] **7. Visualization:** `show_turn` now receives the network (`visualizer.py:24`). In `terminal.py`: `ANSI_COLORS`, `colorize` (`:59`, rainbow and case), `show_network` (`:81`), `show_turn` (`:113`, the order of the state line), `show_summary` (`:137`), `_inside` (`:183`, why it compares positions). Try: make `_inside` return every occupant → `test_show_turn_prints_the_line_then_the_zone_states`.
- [ ] **8. Tests:** `test_referee.py` (the `Referee` class, then the map table), `test_space_time.py` (table tests, planner tests, and `test_every_drone_arrives_when_planned`: why it exists), `test_terminal.py` (the exact state lines, the fake terminal), and the small additions in `test_network.py`, `test_simulator.py`, `test_scheduler.py`, `test_smoke.py`.
- [ ] **9. Edge maps:** read each `maps/edge_*.map` comment and redo the count by hand (3, 5, 7, 2, 501).
- [ ] **10. Makefile:** the `test` rule and the comment; the `visual` rule (7b.9).
- [ ] **11. Step 8 code:** in `main.py`, the three `except` branches (why the printing moved inside the `try`, why `os.dup2` instead of just returning). In `parser.py`, `_strict_int` and `utf-8-sig`. Try: remove `digits.isascii() and` from `_strict_int` → `test_nb_drones_needs_plain_digits[٣]` fails, because `'٣'.isdigit()` is True and `int('٣')` is 3.
- [ ] **12. 7b.4 replay clock, `visualization/playback.py`** (line numbers from 2026-11-09; commit it first, or `git restore` has nothing to bring back): one float `time` counts turns; `turn` is its ceil (`:46`) and `settled` is `frames[floor]` (`:56`), so the counters change when a turn's animation ends. The controls (`:65` to `:110`). `positions` (`:112`): `before.get(drone, start)`, only `after` is drawn, and the `turn == 0` guard (without it `frames[-1]` is the *last* frame; no test can catch its removal, because frame 0 has no poses). `_places` (`:145`): slots by id, the same trick as `on_spot`. Also in `layout.py`: `_scale` moved into the class as a `@staticmethod`. Try: remove `sorted(...)` in `_places` → only `test_drones_inside_a_zone_take_its_slots_by_id` fails (the hand-made frame lists D2 first); `math.ceil` in `settled` → only `test_a_delivered_drone_joins_the_counter_when_its_turn_ends`.
- [ ] **13. 7b.5 the map, `visualization/graphical.py`** (line numbers from 2026-11-09; commit it first): the banner rule (`:24`, and why it needs `# noqa: E402`). `draw` (`:71`): the links glow for the turn on screen, while places and counts show `settled`. The public methods decide what is shown (`count_text` `:95`, `name_label` `:115`, `badge` `:129`, `zone_color` `:146`, `drone_color` `:165` and its golden-ratio hue); the private `_draw_*` methods only paint it. `_draw_link` (`:169`): `(dy, -dx) / length` is the link turned 90°. `_draw_places` (`:231`): why the drones inside take the first places. `_draw_drones` (`:283`): "waited" means the same pose at both ends of the turn. `_fit` (`:343`). Also in `layout.py`: the minimum drone radius went from 5 to 7 px. Try: delete the `os.environ.setdefault` line → only `test_importing_the_view_prints_nothing` fails (the banner reaches stdout); in `draw`, pass `playback.frames[playback.turn]` to `_draw_places` instead of `playback.settled` → only `test_a_place_reserved_by_a_flying_drone_has_a_ring` fails.
- [ ] **14. 7b.5b around the map, `visualization/graphical.py`** (line numbers from 2026-11-10; commit it first): `draw` paints the bars (`:137`), then the panels, the tooltip last so it is on top; the summary only when `playback.time == playback.last` (`:141`). The public texts: `bar_texts` (`:200`, `{speed:g}` writes `x1`, not `x1.0`), `zone_lines` (`:222`, the kind from the class name; why drones resting in the start or the end are not listed), `drone_lines` (`:254`, the same "waited" rule as `_draw_drones`), `tooltip` (`:266`, drones before zones, the one drawn on top first), `summary_lines` (`:284`). The painters: `_draw_bars` (`:475`) and `_draw_panel` (`:499`, `**anchor` goes straight to `get_rect`, `.clamp` keeps the panel in the window). `_fit` (`:552`) keeps its cut texts. Try: in `tooltip`, `reversed(positions)` → `positions` → only `test_the_drone_drawn_on_top_gets_the_tooltip` fails; in `_draw_panel`, drop `.clamp(surface.get_rect())` → only `test_a_tooltip_is_drawn_next_to_the_mouse_inside_the_window`.
- [ ] **15. 7b.6 the window, `visualization/graphical.py`** (line numbers from 2026-11-11; commit it first): the `try: import pygame` (`:40`) that turns a missing pygame into `VisualizationError` (new in `parsing/errors.py`), and why it needs no `# noqa: E402` any more. `FPS` (`:73`). `GraphicalViewer` (`:625`): `run` (`:657`), the loop order tick, events, `update`, draw, flip, what `clock.tick(FPS)` returns (`:672`), and the `finally` (`:679`) that closes pygame on every way out, Ctrl+C included. `handle` (`:682`), `press` (`:691`, one branch per row of §6.2 "Controls"), `resize` (`:723`, `set_mode` only under the minimum), `_open` (`:735`, `display.init()` and not `pygame.init()`), `_mouse` (`:755`). In `tests/test_viewer.py`: the `dummy` driver, why each loop test posts a QUIT last, the stand-in clock, and why the "no pygame" test runs in a subprocess. Try: in `_mouse`, delete the two `get_focused` lines → only `test_the_tooltip_needs_the_mouse_over_the_window` fails; in `press`, `(pygame.K_ESCAPE, pygame.K_q)` → `(pygame.K_ESCAPE,)` → only `test_escape_q_and_closing_the_window_stop_the_loop`.
- [ ] **16. 7b.7 the hook** (line numbers from 2026-11-11; commit it first): `VisualizerGroup` (`visualizer.py:41`): why it is itself a `Visualizer` (the Composite pattern: the simulator never changes), and why the list order is the call order (`:70`, the terminal's summary before the window). `GraphicalVisualizer` (`graphical.py:765`): a `Recorder` that overrides only `show_summary`; `super().show_summary(metrics)` (`:794`) keeps the metrics, then `viewer.run()` (`:798`) waits until the window is closed. Why the network comes with the constructor. In the tests: `_Log` in `tests/test_visualizer.py`, the `_plan` helper (`tests/test_viewer.py:41`), and why the stand-in for `GraphicalViewer.run` is a lambda and not `opened.append`. Try: in `VisualizerGroup.show_summary`, loop over `reversed(self.visualizers)` → only `test_each_call_goes_to_every_visualizer_in_order` fails; in `GraphicalVisualizer.show_summary`, delete the `super().show_summary(metrics)` line → only `test_the_window_opens_only_once_the_run_is_over`.
- [ ] **17. 7b.8 `main.py --visual`** (line numbers from 2026-11-13; commit it first): the `argparse` part (`main.py:35`): `prog`, the positional `map_file`, `store_true`, and why a wrong argument exits with 2 without returning (and what `--help` prints). `on_terminal` (`:47`) and the list of visualizers (`:53`): the terminal first; why `GraphicalVisualizer` is imported inside the `if` (`:59`); why an empty `VisualizerGroup` (`:63`) replaced the `None` checks. `sys.stdout.flush()` (`:70`): a pipe's buffer, and what a reader would see without it. When each error happens: no pygame (at the import, before the run) and no screen (at `group.show_summary`, `:71`, after the lines). In `tests/test_main.py`: `_without_pygame` and `sys.modules["pygame"] = None`; `pytest.raises(SystemExit)`; the `os._exit` trick of the flush test. Try: delete the `sys.stdout.flush()` line → only `test_the_lines_reach_the_reader_before_the_window_opens` fails; move the two `if on_terminal:` lines below the `if args.visual:` block → only `test_on_a_terminal_the_summary_comes_before_the_window`.

Choices you may want to change (decisions, not rules):

- On a terminal the state lines go to stdout between the movement lines; stderr would be the alternative.
- The start shows "0 waiting" even when empty; other empty zones are not shown.
- Connections are listed in adjacency order, not map order (the map order isn't stored).
- "Drones moved per turn" counts a flying drone on both of its turns.
- `arrival_turn` is set in `run()`, so calling `step()` by hand doesn't set it.
- The simulator imports `Scheduler` (for `path_cost`) and `Visualizer` (for the type hint).
- Some tests call private methods (`_plan_all`, `_distances_to_end`, `_moves`).
- The colors themselves: black on light gray, the shades of maroon and darkred.
- `main.py` still catches `NotImplementedError` (8.4 removes it).
