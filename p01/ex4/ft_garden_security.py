class Plant:
    def __init__(self, name, height, age):
        self.name = name
        if height < 0:
            print(f"Invalid height for {name}. Setting height to 0.")
            self.height = 0
        else:
            self.height = height
        if age < 0:
            print(f"Invalid age for {name}. Setting age to 0.")
            self.age = 0
        else:
            self.age = age

    def get_height(self):
        return self.height

    def get_age(self):
        return self.age

    def set_height(self, height):
        if height < 0:
            print(f"Invalid operation attempted: height {height}cm [REJECTED]"
                  "\nSecurity: Negative height rejected\n")
        else:
            self.height = height
            print(f"Height updated: {self.height}cm [OK]")

    def set_age(self, age):
        if age < 0:
            print(f"Invalid operation attempted: age {age} days [REJECTED]\n"
                  "Security: Negative age rejected\n")
            print(f"Current plant: {self.name} "
                  f"({self.height}cm, {self.age} days)")
        else:
            self.age = age
            print(f"Age updated: {self.age} days [OK]")
