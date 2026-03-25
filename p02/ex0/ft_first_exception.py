def input_temperature(temp_str) -> int | None:
    try:
        temp = int(temp_str)
    except ValueError:
        print(f"Caught input_temperature error: invalid literal "
              f"for int() with base 10: '{temp_str}'")
        return None
    print(f"Temperature now is {temp}°C")
    return temp


def test_temperature() -> None:
    print("=== Garden Temperature ===")
    print("\nInput data is '25'")
    input_temperature("25")
    print("\nInput data is 'abc'")
    input_temperature("abc")
    print("\nAll tests completed- program didn't crash!", end='')
