def check_temperature(temp_str):
    try:
        temp = int(temp_str)
    except ValueError:
        print(f"Error: '{temp_str}' is not a valid number")
        return None
    if temp < 0:
        print(f"Error: {temp}°C is too cold for plants (min 0°C)")
        return None
    elif temp > 40:
        print(f"Error: {temp}°C is too hot for plants (max 40°C)")
        return None
    print(f"Temperature {temp}°C is perfect for plants!")
    return temp


def test_temperature():
    print(f"\nTesting temperature: 25")
    check_temperature("25")
    print(f"\nTesting temperature: abc")
    check_temperature("abc")
    print(f"\nTesting temperature: -50")
    check_temperature("-50")
    print(f"\nTesting temperature: 100")
    check_temperature("100")

if __name__ == "__main__":
    print("=== Garden Temperature Checker ===")
    test_temperature()
    print("\nAll tests completed- program didn't crash!", end='')