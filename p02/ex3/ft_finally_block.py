def water_plants(plant_list):
    print("Opening watering system")
    try:
        for plant in plant_list:
            print(f"Watering {plant}")
    except Exception:
        print(f"Error: Cannot water {plant}: invalid plant!")
    finally:
        print("Closing watering system (cleanup)")


def test_watering_system():
    try:
        print("=== Garden Watering System ===")
        plants = ["tomato", "lettuce", "carrots"]
        print("\nTesting normal watering...")
        water_plants(plants)
        print("Watering completed successfully!\n")
        print("Testing with error...")
        plants = ["tomato", "lettuce", 123, None, "carrots"]
        water_plants(plants)
    finally:
        print("\nCleanup always happens, even with errors!")
