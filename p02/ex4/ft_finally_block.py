def water_plants(plant_list):
    print("Opening watering system")
    plants = ["tomato", "lettuce", "carrots"]
    try:
        for plant in plant_list:
            if plant not in plants:
                raise ValueError(f"Invalid plant name: '{plant}'")
            print(f"Watering {plant}: [OK]")
    except ValueError as e:
        print(f"Caught PlantError: {e}")
        print(".. ending tests and returning to main")
    finally:
        print("Closing watering system")


def test_watering_system():
    try:
        print("=== Garden Watering System ===")
        plants = ["tomato", "lettuce", "carrots"]
        print("\nTesting valid plants...")
        water_plants(plants)
        print("\nTesting invalid plants...")
        plants = ["tomato", 123]
        water_plants(plants)
    finally:
        print("\nCleanup always happens, even with errors!")

test_watering_system()