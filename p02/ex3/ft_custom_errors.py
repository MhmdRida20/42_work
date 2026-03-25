class GardenError(Exception):
    pass


class PlantError(GardenError):
    pass


class WaterError(GardenError):
    pass


def test_garden_error():
    try:
        raise GardenError("The tomato plant is wilting!")
    except GardenError as e:
        print(f"Caught a garden error: {e}")
        e = "Not enough water in the tank!"
        print(f"Caught a garden error: {e}")


def test_plant_error():
    try:
        raise PlantError("The tomato plant is wilting!")
    except PlantError as e:
        print(f"Caught PlantError: {e}")


def test_water_error():
    try:
        raise WaterError("Not enough water in the tank!")
    except WaterError as e:
        print(f"Caught WaterError: {e}")


if __name__ == "__main__":
    print("=== Custom Garden Errors Demo ===")
    print("\nTesting PlantError...")
    test_plant_error()
    print("\nTesting WaterError...")
    test_water_error()
    print("\nTesting catching all garden errors...")
    test_garden_error()
    print("\nAll custom error types work correctly!", end='')
