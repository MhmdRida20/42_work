#!/usr/bin/env python3

class Plant:
    def __init__(self, name: str, height: float, age: int) -> None:
        self.name = name
        self.height = float(height)
        self.age = age

    def show(self) -> None:
        print(f"{self.name}: {self.height}cm, {self.age} days old")


def Plant_factory(plant_data: list) -> list[Plant]:
    plants = []
    for plant in plant_data:
        plant = Plant(plant[0], plant[1], plant[2])
        print(f"Created: {plant.name}: {plant.height}cm, {plant.age} days old")
        plants.append(plant)
    return plants


if __name__ == "__main__":
    print("=== Plant Factory Output ===")
    plant_data = [
        ["Rose", 25, 30],
        ["Oak", 200, 365],
        ["Cactus", 5, 90],
        ["Sunflower", 80, 45],
        ["Fern", 15, 120]
    ]
    plants = Plant_factory(plant_data)
    print("\nTotal plants created: ", len(plants))
