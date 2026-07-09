## About

**FuncMage Chronicles** is a 42-curriculum Python project built around five
exercises that progressively cover the core concepts of functional
programming:

| # | Exercise | Concept | File |
|---|----------|---------|------|
| 0 | Lambda Sanctum | Lambda expressions | `ex0/lambda_spells.py` |
| 1 | Higher Realm | Higher-order functions | `ex1/higher_magic.py` |
| 2 | Memory Depths | Closures & lexical scoping | `ex2/scope_mysteries.py` |
| 3 | Ancient Library | `functools` / `operator` | `ex3/functools_artifacts.py` |
| 4 | Master's Tower | Decorators & `@staticmethod` | `ex4/decorator_mastery.py` |

Each exercise is self-contained, testable independently, and ends with a
short reflection on *why* the pattern works — not just *how* to implement it.

---

## Requirements

- Python **3.10** or later
- Code must pass **flake8**
- Type hints on all function signatures and return types
- No `eval()` / `exec()`
- No file I/O
- No global variables (use `nonlocal` inside closures instead)
- No external libraries (standard library only — `functools`, `operator`,
  `typing`, `collections.abc`, `itertools` where authorized per exercise)

---

## Usage

Each exercise can be run directly:

```bash
python3 ex0/lambda_spells.py
python3 ex1/higher_magic.py
python3 ex2/scope_mysteries.py
python3 ex3/functools_artifacts.py
python3 ex4/decorator_mastery.py
```

Each file's `main()` builds its own test data and prints results matching
the expected output format described in the subject.

Or we can use `data_generator.py` to generate fresh randomized test data
(mages, artifacts, spells) for manual testing:

```bash
python3 data_generator.py
```

---

## Project Structure

```
.
├── ex0/
│   └── lambda_spells.py
├── ex1/
│   └── higher_magic.py
├── ex2/
│   └── scope_mysteries.py
├── ex3/
│   └── functools_artifacts.py
├── ex4/
│   └── decorator_mastery.py
└── README.md
```

---

## Resources

Notes, concepts, and small illustrative examples gathered while working
through the project — useful for the peer-review defense.

### Example of wrappers

A **wrapper function** wraps around another function to add behavior
before and/or after it runs, without touching the original function's
logic. Decorators are built on exactly this idea: a decorator is a
function that constructs and returns a wrapper.

```python
def spell_timer(func):
    def wrapper(*args, **kwargs):
        print(f"Casting {func.__name__}...")
        start = time.time()
        result = func(*args, **kwargs)      # call the real function
        elapsed = time.time() - start
        print(f"Spell completed in {elapsed:.3f} seconds")
        return result                        # pass through the real result
    return wrapper
```

When you do:

```python
@spell_timer
def fireball():
    return "Fireball cast!"
```

Python replaces `fireball` with `wrapper`. So calling `fireball()` now
actually calls `wrapper()`, which prints timing info, calls the *real*
`fireball` internally, and returns its result — the "before/after"
behavior gets added transparently.

> Note: without `functools.wraps(func)` on the wrapper, `fireball.__name__`
> would become `"wrapper"` instead of `"fireball"` — the wrapper's identity
> leaks through and hides the original function's metadata.

### Other useful references

- [Python docs — `functools`](https://docs.python.org/3/library/functools.html)
- [Python docs — `operator`](https://docs.python.org/3/library/operator.html)
- [Python docs — `collections.abc`](https://docs.python.org/3/library/collections.abc.html)
- [Real Python — Primer on Python Decorators](https://realpython.com/primer-on-python-decorators/)
- [Real Python — Python Closures](https://realpython.com/python-closures/)

---