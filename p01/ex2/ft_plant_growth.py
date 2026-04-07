#!/usr/bin/env python3

class Plant:
    def __init__(self, name: str, height: float, plant_age: int) -> None:
        self.name = name
        self.height = height
        self.plant_age = plant_age
        self.growth = 0.0

    def grow(self) -> None:
        self.height += 1.0
        self.growth += 1.0

    def age(self, i: int) -> None:
        self.plant_age += i

    def get_info(self) -> str:
        return f"{self.name}: {self.height}cm, {self.plant_age} days old"


rose = Plant("Rose", 25.0, 30)
print("=== Garden Plant Growth ===")
print(rose.get_info())
for day in range(7):
    rose.grow()
    rose.age(1)
    print(f"=== Day {day + 1} ===")
    print(rose.get_info())
print(f"Growth this week: {rose.growth}cm")
