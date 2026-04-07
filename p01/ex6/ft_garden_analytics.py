#!/usr/bin/env python3

class Plant:
    def __init__(self, name: str, height: float, age: int) -> None:
        self.name = name
        self.height = height
        self.age = age
        self._stats = Plant.PlantStats()

    class PlantStats:
        def __init__(self) -> None:
            self._grow_count = 0
            self._age_count = 0
            self._show_count = 0

        def increment_grow(self) -> None:
            self._grow_count += 1

        def increment_age(self) -> None:
            self._age_count += 1

        def increment_show(self) -> None:
            self._show_count += 1

        def display(self) -> str:
            return f"Stats: {self._grow_count} grow, {self._age_count} age, " \
                   f"{self._show_count} show"

    def show(self) -> str:
        self._stats.increment_show()
        return f"{self.name}: {self.height}cm, {self.age} days old"

    def grow(self, length: float = 8.0) -> None:
        self._stats.increment_grow()
        self.height += length

    def age_plant(self, days: int = 1) -> None:
        self._stats.increment_age()
        self.age += days

    @staticmethod
    def is_older_than_year(age: int) -> bool:
        return age > 365

    @classmethod
    def create_anonymous(cls) -> "Plant":
        return cls("Unknown plant", 0.0, 0)


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


class Seed(Flower):
    def __init__(self, name: str, height: float, age: int, color: str) -> None:
        super().__init__(name, height, age, color)
        self.seeds = 0

    def show(self) -> str:
        base_info = super().show()
        return f"{base_info}\nSeeds: {self.seeds}"

    def bloom(self) -> None:
        super().bloom()
        self.seeds = 42


class Tree(Plant):
    def __init__(self, name: str, height: float, age: int,
                 trunk_diameter: float) -> None:
        super().__init__(name, height, age)
        self.trunk_diameter = trunk_diameter
        self._stats = Tree.TreeStats()

    class TreeStats(Plant.PlantStats):
        def __init__(self) -> None:
            super().__init__()
            self._shade_count = 0

        def increment_shade(self) -> None:
            self._shade_count += 1

        def display(self) -> str:
            base_display = super().display()
            return f"{base_display}\n{self._shade_count} shade"

    def show(self) -> str:
        base_info = super().show()
        return f"{base_info}\nTrunk diameter: {self.trunk_diameter}cm"

    def produce_shade(self) -> str:
        self._stats.increment_shade()
        shade_length = self.height
        shade_width = self.trunk_diameter
        return f"Tree {self.name} now produces a shade of {shade_length}" \
               f"cm long and {shade_width}cm wide."


def display_stats(plant: Plant) -> None:
    print(plant._stats.display())


if __name__ == "__main__":
    print("=== Garden statistics ===")

    print("=== Check year-old")
    print(f"Is 30 days more than a year? -> {Plant.is_older_than_year(30)}")
    print(f"Is 400 days more than a year? -> {Plant.is_older_than_year(400)}")
    print("=== Flower")
    rose = Flower("Rose", 15.0, 10, "red")
    print(rose.show())
    print("[statistics for Rose]")
    display_stats(rose)
    print("[asking the rose to grow and bloom]")
    rose.grow()
    rose.bloom()
    print(rose.show())
    print("[statistics for Rose]")
    display_stats(rose)

    # Tree
    print("=== Tree")
    oak = Tree("Oak", 200.0, 365, 5.0)
    print(oak.show())
    print("[statistics for Oak]")
    display_stats(oak)
    print("[asking the oak to produce shade]")
    print(oak.produce_shade())
    print("[statistics for Oak]")
    display_stats(oak)

    # Seed
    print("=== Seed")
    sunflower = Seed("Sunflower", 80.0, 45, "yellow")
    print(sunflower.show())
    print("[make sunflower grow, age and bloom]")
    sunflower.grow(30.0)
    sunflower.age_plant(20)
    sunflower.bloom()
    print(sunflower.show())
    print("[statistics for Sunflower]")
    display_stats(sunflower)

    # Anonymous
    print("=== Anonymous")
    anonymous_plant = Plant.create_anonymous()
    print(anonymous_plant.show())
    print("[statistics for Unknown plant]")
    display_stats(anonymous_plant)
