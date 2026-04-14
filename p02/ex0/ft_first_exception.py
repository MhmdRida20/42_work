#!/usr/bin/env python3

def input_temperature(temp_str: str) -> int | None:
    try:
        temp = int(temp_str)
    except ValueError:
        print(f"Caught input_temperature error: invalid literal for int() with base 10: '{temp_str}'")
        return None
    print(f"Temperature is now {temp}°C")
    return temp


def test_temperature() -> None:
    print("=== Garden Temperature ===\n")

    temp = "25"
    print(f"Input data is '{temp}'")
    input_temperature(temp)
    temp = "abc"
    print(f"\nInput data is '{temp}'")
    input_temperature(temp)
    print("All tests completed- program didn't crash!", end='')


if __name__ == "__main__":
    test_temperature()
