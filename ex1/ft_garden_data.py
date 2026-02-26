class Plant:
    def __init__(self, name, height, age):
        self.name = name
        self.height = height
        self.age = age


rose = Plant("Rose", 25, 30)
sunflower = Plant("Sunflower", 80, 45)
cactus = Plant("Cactus", 15, 120)

plants = [rose, sunflower, cactus]
print("=== Garden Plant Registry ===")
for plant in range(len(plants)):
    print(f"{plants[plant].name}: {plants[plant].height}cm"
          f", {plants[plant].age} days old")
