class Plant:
    def __init__(self, name, height, age):
        self.name = name
        self.height = height
        self.age = age

    def print_info(self):
        return f"{self.name}"


class Flower(Plant):
    def __init__(self, name, height, age, color):
        super().__init__(name, height, age)
        self.color = color

    def print_info(self):
        return super().print_info() + " (Flower): " \
         f"{self.height}cm, {self.age} days, {self.color} color" \
         f"\n{self.bloom()}"

    def bloom(self):
        return f"{self.name} is blooming beautifully!"


class Tree(Plant):
    def __init__(self, name, height, age, diameter):
        super().__init__(name, height, age)
        self.diameter = diameter

    def print_info(self):
        return super().print_info() + " (Tree): " \
         f"{self.height}cm, {self.age} days, {self.diameter}cm diameter" \
         f"\n{self.produce_shade()}"

    def produce_shade(self):
        volume = 3.14 * (self.diameter / 2) ** 2 * (self.height / 100)
        return f"{self.name} provides {int(volume)} square meters of shade."


class Vegetable(Plant):
    def __init__(self, name, height, age, harvest_season, nutritional_value):
        super().__init__(name, height, age)
        self.harvest_season = harvest_season
        self.nutritional_value = nutritional_value

    def print_info(self):
        return super().print_info() + " (Vegetable): " \
         f"{self.height}cm, {self.age} days, {self.harvest_season} harvest" \
         f"\n{self.show_nutritional_value()}"

    def show_nutritional_value(self):
        return f"{self.name} is rich in {self.nutritional_value}."


if __name__ == "__main__":
    print("=== Garden Plant Types ===")
    rose = Flower("Rose", 25, 30, "red")
    tulip = Flower("Tulip", 20, 25, "yellow")
    oak = Tree("Oak", 500, 1825, 50)
    pine = Tree("Pine", 400, 1500, 40)
    tomato = Vegetable("Tomato", 80, 90, "summer", "vitamin C")
    carrot = Vegetable("Carrot", 30, 70, "spring", "vitamin A")
    plants = [rose, tulip, oak, pine, tomato, carrot]
    for plant in plants:
        print(plant.print_info())
