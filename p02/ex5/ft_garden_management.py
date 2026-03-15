class GardenError(Exception):
    pass

# def raise_garden_error():
#     try:
#         raise GardenError("Not enough water in the tank!")
#     except GardenError as e:
#         print(f"Caught GardenError: {e}")

class Plant:
    def __init__(self, name : str, water_level : int,
                 sunlight_hours : int) -> None:
        try:
            if not name:
                raise ValueError("Plant name cannot be empty")
            if water_level > 10:
                raise ValueError(
                f"Water level {water_level} is too high (max 10)")
            if water_level < 1:
                raise ValueError(
                f"Water level {water_level} is too low (min 1)")
            if sunlight_hours > 12:
                raise ValueError(
                f"Sunlight hours {sunlight_hours} is too high (max 12)")
            if sunlight_hours < 2:
                raise ValueError(
                f"Sunlight hours {sunlight_hours} is too low (min 2)")
            self.name = name
            self.water_level = water_level
            self.sunlight_hours = sunlight_hours
        except ValueError as e:
            print(f"Error: {e}")
            return


class GardenManager:
    def __init__(self) -> None:
        self.plants = []
        self.tank = 0
        
    def add_plant(self, name: str, water_level: int,
                  sunlight_hours: int) -> None:
        try:
            plant = Plant(name, water_level, sunlight_hours)
            self.plants.append(plant)
            print(f"Added {plant.name} successfully!")
        except ValueError as e:
            print(f"Error adding plant: {e}")
    
    def water_plants(self) -> None:
        print("Opening watering system")
        try:
            for plant in self.plants:
                print(f"Watering {plant.name} - success")
        except Exception as e:
            print(f"Error watering plants: {e}")
        finally:
            print("Closing watering system (cleanup)")
    
    def check_plants_health(self) -> None:
        print("Checking plant health...")
        try:
            for plant in self.plants:
                if plant.water_level < 1:
                        message = f"Water level {plant.water_level} is too low (min 1)"
                        raise ValueError(message)
                if plant.water_level > 10:
                    message = f"Water level {plant.water_level} is too high (max 10)"
                    raise ValueError(message)
                if plant.sunlight_hours < 2:
                    message = f"Sunlight hours {plant.sunlight_hours} is too low (min 2)"
                    raise ValueError(message)
                if plant.sunlight_hours > 12:
                    message = f"Sunlight hours {plant.sunlight_hours} is too high (max 12)"
                    raise ValueError(message)
                print(
                    f"{plant.name}: healthy"
                    f" (water: {plant.water_level},"
                    f" sun: {plant.sunlight_hours})"
                )
        except ValueError as e:
            print(f"Error checking plant health: {e}")

    def test_error_recovery(self) -> None:
        try:
            if self.tank < 1:
                raise GardenError("Not enough water in tank")
        except GardenError as e:
            print(f"Caught GardenError: {e}")
        finally:
            print("System recovered and continuing...")
        
def test_garden_management() -> None:
    print("=== Garden Management System ===")
    manager = GardenManager()

    print("\nAdding plants to garden...")
    manager.add_plant("tomato", 5, 8)
    manager.add_plant("lettuce", 15, 6)  # water too high — added but health fails
    manager.add_plant("", 5, 6)          # invalid name

    print("\nWatering plants...")
    manager.water_plants()

    print("\nChecking plant health...")
    manager.check_plants_health()

    print("\nTesting error recovery...")
    manager.test_error_recovery()

    print("\nGarden management system test complete!")


if __name__ == "__main__":
    test_garden_management()