#!/usr/bin/env python3

class PlantError(Exception):
    pass


def water_plant(plant_name: str) -> None:
    if plant_name != plant_name.capitalize():
        raise PlantError(f"Invalid plant name to water: '{plant_name}'")
    print(f"Watering {plant_name}: [OK]")


def test_watering_system() -> None:
    test_plants = ["Tomato", "Lettuce", "Carrots", "lettuce"]
    print("=== Garden Watering System ===")

    try:
        print("Opening watering system")
        for plant in test_plants:
            water_plant(plant)
    except PlantError as e:
        print(f"Caught PlantError: {e}")
        print(".. ending tests and returning to main")
    finally:
        print("Closing watering system")


if __name__ == "__main__":
    test_watering_system()
