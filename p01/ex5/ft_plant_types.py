#!/usr/bin/env python3

class Plant:
    def __init__(self, name: str, height: float, age: int) -> None:
        self.name = name
        self.height = height
        self.age = age

    def show(self) -> str:
        return f"{self.name}: {self.height:.1f}cm, {self.age} days old"

    def grow(self, length: float = 10.0) -> None:
        self.height += length

    def age_plant(self, days: int = 1) -> None:
        self.age += days


class Flower(Plant):
    def __init__(self, name: str, height: float, age: int, color: str) -> None:
        super().__init__(name, height, age)
        self.color = color
        self.is_blooming = False

    def show(self) -> str:
        base_info = super().show()
        if not self.is_blooming:
            bloom_status = "has not bloomed yet"
        else:
            bloom_status = "is blooming beautifully!"
        return f"{base_info}\nColor: {self.color}\n{self.name} {bloom_status}"

    def bloom(self) -> None:
        self.is_blooming = True


class Tree(Plant):
    def __init__(self, name: str, height: float, age: int,
                 trunk_diameter: float) -> None:
        super().__init__(name, height, age)
        self.trunk_diameter = trunk_diameter

    def show(self) -> str:
        base_info = super().show()
        return f"=== Tree\n{base_info}\n" \
               f"Trunk diameter: {self.trunk_diameter}cm"

    def produce_shade(self) -> str:
        shade_length = self.height
        shade_width = self.trunk_diameter
        return f"Tree {self.name} now produces a shade of {shade_length}" \
               f"cm long and {shade_width}cm wide."


class Vegetable(Plant):
    def __init__(self, name: str, height: float,
                 age: int, harvest_season: str) -> None:
        super().__init__(name, height, age)
        self.harvest_season = harvest_season
        self.nutritional_value = 0

    def show(self) -> str:
        base_info = super().show()
        return f"{base_info}\nHarvest season: {self.harvest_season}\n" \
               f"Nutritional value: {self.nutritional_value}"

    def grow(self, length: float = 10.0) -> None:
        super().grow(length)

    def age_plant(self, days: int = 1) -> None:
        super().age_plant(days)
        self.nutritional_value += days


if __name__ == "__main__":
    print("=== Garden Plant Types ===")

    # Flower
    print("=== Flower")
    rose = Flower("Rose", 15.0, 10, "red")
    print(rose.show())
    print("[asking the rose to bloom]")
    rose.bloom()
    print(rose.show())

    print()

    # Tree
    oak = Tree("Oak", 200.0, 365, 5.0)
    print(oak.show())
    print("[asking the oak to produce shade]")
    print(oak.produce_shade())

    print()

    # Vegetable
    print("=== Vegetable")
    tomato = Vegetable("Tomato", 5.0, 10, "April")
    print(tomato.show())
    print("[make tomato grow and age for 20 days]")
    for _ in range(20):
        tomato.grow(2.1)
        tomato.age_plant()
    print(tomato.show())
