#!/usr/bin/env python3

def input_temperature(temp_str: str) -> int:
    temp = int(temp_str)
    if temp > 40:
        raise ValueError(f"{temp}°C is too hot for plants (max 40°C)\n")
    if temp < 0:
        raise ValueError(f"{temp}°C is too cold for plants (min 0°C)\n")
    print(f"Temperature now is {temp}°C\n")
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
    print("=== Garden Temperature ===\n")

    test_cases = ["25", "abc", "100", "-50"]
    for val in test_cases:
        print(f"Input data is '{val}'")
        try:
            input_temperature(val)
        except ValueError as e:
            print(f"Caught input_temperature error: {e}\n")

    print("All tests completed- program didn't crash!", end='')


if __name__ == "__main__":
    test_temperature()
