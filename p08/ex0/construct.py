import sys


def is_venv() -> bool:
    return sys.prefix != sys.base_prefix


def print_venv_info() -> None:
    print("Welcome to the construct\n")

    print(f"Current Python: {sys.executable}")
    print(f"Virtual Environment: {sys.prefix}")
    print(f"Environment Path: {sys.path[0]}\n")
    print("""
SUCCESS: You're in an isolated environment!
Safe to install packages without affecting
the global system.""")
    print(f"\nPackage installation path:\n {sys.prefix}"
          "/lib/python"
          f"{sys.version_info.major}.{sys.version_info.minor}/site-packages")


def print_not_venv_info() -> None:
    print("You're still plugged in")
    print(f"Current Python: {sys.executable}")
    print("Virtual Environment: None detected")
    print("""
WARNING: You're in the global environment!
The machines can see everything you install.

To enter the construct, run:
python -m venv matrix_env
source matrix_env/bin/activate # On Unix
matrix_env\\Scripts\\activate # On Windows\n
Then run this program again.""")


if __name__ == "__main__":
    print("\nMATRIX STATUS: ", end="")
    if is_venv():
        print_venv_info()
    else:
        print_not_venv_info()
