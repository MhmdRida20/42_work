_This project has been created as part of the 42 curriculum by mrida_

# Code Cultivation - Object-Oriented Garden Systems

## Evaluator Instructions

### Checking code standards
```bash
flake8      # style linter
mypy ./     # type checker...existing code...
### Checking code standards
```bash
flake8      # style linter
mypy ./     # type checker
```

---

## Exercises

### ex0: Command Quest (`ft_command_quest.py`)
Introduces command-line argument handling using the `sys` module. It parses arguments passed to the script, counts them, and dynamically prints each argument alongside its index.

### ex1: Score Analytics (`ft_score_analytics.py`)
A script that takes numeric scores as command-line arguments, safely processes them using `try/except` blocks to handle `ValueError`s, and calculates vital statistics such as total score, average, high/low scores, and range.

### ex2: Coordinate System (`ft_coordinate_system.py`)
Handles user input formatting for 3D coordinates (X, Y, Z). It parses the inputs into floats and utilizes the `math` module to calculate the geometric distance between points in a 3D space.

### ex3: Achievement Tracker (`ft_achievement_tracker.py`)
Explores Python `set` operations. It randomly assigns achievements to players and uses set logic (unions, intersections, differences) to find shared achievements, unique achievements, and missing ones.

### ex4: Inventory System (`ft_inventory_system.py`)
Focuses on Python dictionaries. It parses items and quantities (`item:quantity`) from command-line arguments, populates an inventory dictionary, and dynamically computes stock percentages, totals, and the most/least abundant items.

### ex5: Data Stream (`ft_data_stream.py`)
Introduces `yield` and generator functions. It simulates an endless game data stream of events, showing how to safely consume and generate data sequences lazily utilizing `typing.Generator`/`typing.Iterator`.

### ex6: Data Alchemist (`ft_data_alchemist.py`)
Demonstrates list and dictionary comprehensions. It processes lists of strings (capitalization checking), generates randomized scores based on filtered data, and filters dictionaries to find high-performing scores against calculated averages.