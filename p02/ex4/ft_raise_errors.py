def check_plant_health(plant_name, water_level, sunlight_hours):
    errors = 0
    try:
        if not plant_name:
            errors += 1
            raise ValueError("Plant name cannot be empty!")
        if not 0 < water_level < 11:
            errors += 1
            level = "high" if water_level > 10 else "low"
            message = f"Water level {water_level} is too {level} "
            message += "(max 10)" if water_level > 10 else "(min 1)"
            raise ValueError(message)
        if not 1 < sunlight_hours < 13:
            errors += 1
            level = "high" if sunlight_hours > 12 else "low"
            message = f"Sunlight hours {sunlight_hours} is too {level} "
            message += "(max 12)" if sunlight_hours > 12 else "(min 2)"
            raise ValueError(message)
    except ValueError as e:
        print(f"Error: {e}")
    finally:
        if errors == 0:
            print(f"Plant '{plant_name}' is healthy")


def test_plant_checks():
    print("=== Plant Health Check ===")
    print("\nTesting good values...")
    check_plant_health("Fern", 5, 6)
    print("\nTesting empty plant name...")
    check_plant_health("", 5, 6)
    print("\nTesting bad water level...")
    check_plant_health("Cactus", 15, 6)
    print("\nTesting bad sunlight hours...")
    check_plant_health("Fern", 5, 0)
    print("\nAll error raising tests completed!")
