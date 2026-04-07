#!/usr/bin/env python3

class Plant:
    def __init__(self, name: str, height: float, age: int) -> None:
        self.name = name
        if height < 0:
            print(f"Invalid height for {name}. Setting height to 0.")
            self.height = 0.0
        else:
            self.height = height
        if age < 0:
            print(f"Invalid age for {name}. Setting age to 0.")
            self.age = 0
        else:
            self.age = age

    def get_height(self) -> float:
        return self.height

    def get_age(self) -> int:
        return self.age

    def set_height(self, height: float) -> None:
        if height < 0:
            print("Rose: Error, height can't be negative\n"
                  "Height update rejected")
        else:
            self.height = height
            print(f"Height updated: {self.height}cm")

    def set_age(self, age: int) -> None:
        if age < 0:
            print("Rose: Error, age can't be negative\n"
                  "Age update rejected\n")
        else:
            self.age = age
            print(f"Age updated: {self.age} days\n")

    def state(self) -> None:
        print(f"Current state: {self.name}: "
              f"{self.height:.1f}cm, {self.age} days old")


if __name__ == "__main__":
    print("=== Garden Security System ===")
    rose = Plant("Rose", 15.0, 10)
    print(f"Plant created: {rose.name}: {rose.get_height()}"
          f"cm, {rose.get_age()} days old\n")
    rose.set_height(25)
    rose.set_age(30)
    rose.set_height(-42)
    rose.set_age(-42)
    rose.state()
