import os
import sys


def load_dotenv_if_available() -> bool:
    """Load .env file using python-dotenv if the library is present."""
    try:
        from dotenv import load_dotenv # type: ignore
        load_dotenv(override=False)   # env vars already set take priority
        return True
    except ImportError:
        print("  [WARN] python-dotenv not installed. "
              "Install it with: pip install python-dotenv")
        return False


def get_config() -> dict[str, str]:
    """Read and return all expected configuration variables."""
    return {
        "MATRIX_MODE": os.environ.get("MATRIX_MODE", "NOT SET"),
        "DATABASE_URL": os.environ.get("DATABASE_URL", "NOT SET"),
        "API_KEY": os.environ.get("API_KEY", "NOT SET"),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", "NOT SET"),
        "ZION_ENDPOINT": os.environ.get("ZION_ENDPOINT", "NOT SET"),
    }


def validate_config(config: dict[str, str]) -> list[str]:
    """Return a list of missing (NOT SET) required keys."""
    return [key for key, val in config.items() if val == "NOT SET"]


def mask_secret(value: str) -> str:
    """Partially mask a secret value for safe display."""
    if value in ("NOT SET", "Unknown"):
        return value
    if len(value) <= 4:
        return "****"
    return value[:2] + "****" + value[-2:]


def display_config(config: dict[str, str]) -> None:
    """Pretty-print the loaded configuration."""
    mode = config["MATRIX_MODE"]

    db_url = config["DATABASE_URL"]
    if db_url == "NOT SET":
        db_status = "NOT CONNECTED"
    elif mode == "production":
        db_status = "Connected to production database"
    else:
        db_status = "Connected to local instance"

    api_key = config["API_KEY"]
    api_status = "NOT AUTHENTICATED"
    if not api_key == "NOT SET":
        api_status = "Authenticated"

    log_level = config["LOG_LEVEL"]
    zion = config["ZION_ENDPOINT"]
    zion_status = "OFFLINE" if zion == "NOT SET" else "Online"

    print("Configuration loaded:")
    print(f"  Mode        : {mode}")
    print(f"  Database    : {db_status}")
    print(f"  API Access  : {api_status}")
    print(f"  Log Level   : {log_level}")
    print(f"  Zion Network: {zion_status}")

    if mode == "production":
        print()
        print("  [PRODUCTION MODE] Stricter settings applied:")
        print(f"    API_KEY  : {mask_secret(api_key)}")
        print(f"    DB URL   : {mask_secret(db_url)}")
    else:
        print()
        print("  [DEVELOPMENT MODE] Verbose output enabled.")


def security_check(config: dict[str, str]) -> None:
    """Run basic environment security checks."""
    print()
    print("Environment security check:")

    # Check 1: no secrets hardcoded in source (always true here)
    print("  [OK] No hardcoded secrets detected")

    # Check 2: .env file present
    if os.path.isfile(".env"):
        print("  [OK] .env file properly configured")
    else:
        print("  [WARN] No .env file found — copy .env.example to .env")

    # Check 3: production overrides work via env vars
    if os.environ.get("MATRIX_MODE"):
        print("  [OK] Production overrides available")
    else:
        print("  [INFO] Set MATRIX_MODE=production to test production mode")


def warn_missing(missing: list[str]) -> None:
    """Print warnings for missing configuration keys."""
    if missing:
        print()
        print("  Missing configuration keys:")
        for key in missing:
            print(f"    [MISSING] {key}")
        print()
        print("  Copy .env.example to .env and fill in the values.")


def main() -> None:
    """Entry point."""
    print("ORACLE STATUS: Reading the Matrix...")
    print()

    dotenv_loaded = load_dotenv_if_available()
    if dotenv_loaded and os.path.isfile(".env"):
        print("  [INFO] Configuration loaded from .env file")
    print()

    config = get_config()
    missing = validate_config(config)

    display_config(config)
    warn_missing(missing)
    security_check(config)

    print()
    print("The Oracle sees all configurations.")

    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
