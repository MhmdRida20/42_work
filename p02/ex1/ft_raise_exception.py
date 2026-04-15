#!/usr/bin/env python3

def input_temperature(temp_str: str) -> int | None:
    try:
        temp = int(temp_str)
        if not (-1 < temp < 41):
            concat_str = "hot" if temp >= 40 else "cold"
            limit_temp_str = "(max 40°C)" if temp >= 40 else "(min 0°C)"
            raise Exception(f"Temperature {temp}°C is"
                            f" too {concat_str} for plants {limit_temp_str}")
    except ValueError:
        print(f"Caught input_temperature error: invalid literal "
              f"for int() with base 10: '{temp_str}'")
        return None
    except Exception as e:
        print(f"Caught input_temperature error: {e}")
        return None
    print(f"Temperature now is {temp}°C")
    return temp


def test_temperature() -> None:
    print("=== Garden Temperature ===")
    print("\nInput data is '25'")
    input_temperature("25")
    print("\nInput data is 'abc'")
    input_temperature("abc")
    print("\nInput data is '100'")
    input_temperature("100")
    print("\nInput data is '-50'")
    input_temperature("-50")
    print("\nAll tests completed- program didn't crash!", end='')
