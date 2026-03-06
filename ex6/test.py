class Plant:
    def __init__(self, name, height, age):
        self.name = name
        self.height = height
        self._age = age

    def grow(self):
        self.height += 1
        print(f"{self.name} grew 1cm")

    def age(self):
        self._age += 1

    def get_info(self):
        return f"{self.name}: {self.height}cm"


class FloweringPlant(Plant):
    def __init__(self, name, height, age, color):
        super().__init__(name, height, age)
        self.color = color
        self.blooming = True

    def get_info(self):
        status = "blooming" if self.blooming else "not blooming"
        return f"{self.name}: {self.height}cm, {self.color} flowers ({status})"


class PrizeFlower(FloweringPlant):
    def __init__(self, name, height, age, color, prize_points):
        super().__init__(name, height, age, color)
        self.prize_points = prize_points

    def get_info(self):
        status = "blooming" if self.blooming else "not blooming"
        return (f"{self.name}: {self.height}cm, {self.color} flowers "
                f"({status}), Prize points: {self.prize_points}")


class GardenManager:
    all_gardens = []

    class GardenStats:
        def __init__(self, plants):
            self.plants = plants

        def total_growth(self):
            return len(self.plants)

        def count_by_type(self):
            regular = sum(1 for p in self.plants
                          if type(p) is Plant)
            flowering = sum(1 for p in self.plants
                            if type(p) is FloweringPlant)
            prize = sum(1 for p in self.plants
                        if type(p) is PrizeFlower)
            return regular, flowering, prize

        def score(self):
            total = 0
            for p in self.plants:
                total += p.height
                if isinstance(p, PrizeFlower):
                    total += p.prize_points
            return total

    def __init__(self, owner):
        self.owner = owner
        self.plants = []
        GardenManager.all_gardens.append(self)

    def add_plant(self, plant):
        self.plants.append(plant)
        print(f"Added {plant.name} to {self.owner}'s garden")

    def grow_all(self):
        print(f"\n{self.owner} is helping all plants grow...")
        for plant in self.plants:
            plant.grow()

    def report(self):
        stats = GardenManager.GardenStats(self.plants)
        regular, flowering, prize = stats.count_by_type()

        print(f"\n=== {self.owner}'s Garden Report ===")
        print("Plants in garden:")
        for plant in self.plants:
            print(f"- {plant.get_info()}")
        print(f"\nPlants added: {len(self.plants)}, "
              f"Total growth: {stats.total_growth()}cm")
        print(f"Plant types: {regular} regular, {flowering} flowering, "
              f"{prize} prize flowers")

    @classmethod
    def create_garden_network(cls):
        print("\nGarden scores - ", end="")
        scores = []
        for garden in cls.all_gardens:
            stats = cls.GardenStats(garden.plants)
            scores.append(f"{garden.owner}: {stats.score()}")
        print(", ".join(scores))
        print(f"Total gardens managed: {len(cls.all_gardens)}")

    @staticmethod
    def validate_height(height):
        return height > 0


# === Main ===
print("=== Garden Management System Demo ===\n")

alice_garden = GardenManager("Alice")
bob_garden = GardenManager("Bob")

oak = Plant("Oak Tree", 100, 365)
rose = FloweringPlant("Rose", 25, 30, "red")
sunflower = PrizeFlower("Sunflower", 50, 45, "yellow", 10)

alice_garden.add_plant(oak)
alice_garden.add_plant(rose)
alice_garden.add_plant(sunflower)

tulip = FloweringPlant("Tulip", 30, 20, "pink")
bamboo = Plant("Bamboo", 60, 180)
bob_garden.add_plant(tulip)
bob_garden.add_plant(bamboo)

alice_garden.grow_all()
bob_garden.grow_all()

alice_garden.report()
bob_garden.report()

print(f"\nHeight validation test: {GardenManager.validate_height(50)}")
GardenManager.create_garden_network()
