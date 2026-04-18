#!/usr/bin/env python3

class GardenError(Exception):
    def __init__(self, message: str = "Unknown garden error") -> None:
        super().__init__(message)


class PlantError(GardenError):
    def __init__(self, message: str = "Unknown plant error") -> None:
        super().__init__(message)


class WaterError(GardenError):
    def __init__(self, message: str = "Unknown water error") -> None:
        super().__init__(message)


def test_garden_error() -> None:
    try:
        raise GardenError("This is a garden error")
    except GardenError as e:
        print(f"Caught a garden error: {e}")


def test_plant_error() -> None:
    try:
        raise PlantError("This is a plant error")
    except PlantError as e:
        print(f"Caught PlantError: {e}")


def test_water_error() -> None:
    try:
        raise WaterError("This is a water error")
    except WaterError as e:
        print(f"Caught WaterError: {e}")


if __name__ == "__main__":
    print("=== Custom Garden Errors Demo ===")
    print("Testing PlantError...")
    test_plant_error()
    print("Testing WaterError...")
    test_water_error()
    print("Testing catching all garden errors...")
    test_garden_error()
