import sys

# Authorized: import sys, sys.argv, len(), print(), sum(), list(), round(),
# dict.keys(), dict.values(),` dict.update()`


def ft_inventory_system():
    if len(sys.argv) < 2:
        print("Usage: python ft_inventory_system.py <item1> <item2> ...")
        return
    inventory = {}
    number_added = 0
    for item in sys.argv[1:]:
        if item in inventory:
            print(f"Redundant item '{item}' - discarding")
        elif ":" not in item:
            print(f"Error - invalid parameter '{item}'")
        else:
            try:
                name, quantity = item.split(":")
                inventory[name] = inventory.get(name, int(quantity))
                number_added += 1
            except ValueError:
                print(f"Quantity error for '{name}': invalid "
                      f"literal for int() with base 10: '{quantity}'")
    print("Got inventory: {", end="")
    for item, quantity in inventory.items():
        print(f" {item}: {quantity}", end=", "
              if item != list(inventory.keys())[-1] else "")
    print("}")
    item_list = list(inventory.keys())
    print(f"Item list: {item_list}")

    print(f"Total quantity of the {len(inventory)}"
          f" items: {sum(inventory.values())}")
    for item in inventory.keys():
        print(f"Item {item} represents "
              f"{round((inventory[item] / sum(inventory.values())) * 100)}%")
    print(f"Item most abundant: {max(inventory, key=inventory.get)} "
          f"with quantity {max(inventory.values())}")
    print(f"Item least abundant: {min(inventory, key= inventory.get)} "
          f"with quantity {min(inventory.values())}")
    inventory.update({'magic_item': 1})
    print("Updated inventory: ", inventory)


if __name__ == "__main__":
    ft_inventory_system()
