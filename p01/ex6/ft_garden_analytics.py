class Plant:
    def __init__(self, name, height, age):
        self.name = name
        self.height = height
        self.age = age
        self.growth = 0

    def print_info(self):
        return f"{self.name}"

    def grow(self):
        self.height += 1
        self.growth += 1
        print(f"{self.name} grew 1cm")

    def inc_age(self):
        self.age += 1


class FloweringPlant(Plant):
    def __init__(self, name, height, age, color):
        super().__init__(name, height, age)
        self.color = color
        self.blooming = True

    def print_info(self):
        status = "blooming" if self.blooming else "not blooming"
        return f"{self.name}: {self.height}cm, {self.color} flowers ({status})"

    def bloom(self):
        self.blooming = True

    def wilt(self):
        self.blooming = False


class PrizeFlower(FloweringPlant):
    def __init__(self, name, height, age, color, prize_points):
        super().__init__(name, height, age, color)
        self.prize_points = prize_points

    def print_info(self):
        status = "blooming" if self.blooming else "not blooming"
        return (f"{self.name}: {self.height}cm, {self.color} flowers "
                f"({status}), Prize points: {self.prize_points}")


class GardenManager:
    all_gardens = []

    class GardenStats:
        def __init__(self, plants):
            self.plants = plants

        def total_growth(self):
            return sum(p.growth for p in self.plants)

        def count_by_type(self):
            regular = sum(1 for p in self.plants if type(p) is Plant)
            flowering = sum(1 for p in self.plants
                            if type(p) is FloweringPlant)
            prize = sum(1 for p in self.plants if type(p) is PrizeFlower)
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

    def grow_help(self):
        print(f"{self.owner} is helping all plants grow...")
        for plant in self.plants:
            plant.grow()

    def validate_height(self):
        for plant in self.plants:
            if plant.height > 115 or plant.height < 0:
                return False
        return True

    def report(self):
        print(f"\n=== {self.owner}'s Garden Report ===")
        print(f"Plants in garden:")
        for plant in self.plants:
            print(f" - {plant.print_info()}")
        stats = GardenManager.GardenStats(self.plants)
        regular, flowering, prize = stats.count_by_type()
        print(f"High validation test: {self.validate_height()}")
#        print(f"Garden scores - {', '.join(f'{manager.owner}: {GardenManager.GardenStats(manager.plants).score()}' 
#                                           for manager in GardenManager.all_gardens)}")
        print(f"Garden scores -")
        for manager in GardenManager.all_gardens:
            score = GardenManager.GardenStats(manager.plants).score()
            print(f" - {manager.owner}: {score}")
        print(f"Total gardens managed: {len(GardenManager.all_gardens)}")

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
print("hi")
bob_garden.add_plant(bamboo)
print("hi")
alice_garden.grow_help()
bob_garden.grow_help()
alice_garden.report()
bob_garden.report()
print(f"\nHeight validation test: {alice_garden.validate_height()}")
