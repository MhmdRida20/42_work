class Plant:
    def __init__(self, name, height, age):
        self.name = name
        self.height = height
        self.age = age


def Plant_factory(plant_data):
    plants = []
    for plant in plant_data:
        plant = Plant(plant[0], plant[1], plant[2])
        print(f"Created: {plant.name}, ({plant.height}cm, {plant.age} days)")
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
