# !/usr/bin/env python3

import math


def get_player_pos() -> tuple:
    tuple_string = input("Enter new coordinates as floats in format 'x,y,z': ")
    tuple_string = tuple_string.split(",")
    if len(tuple_string) != 3:
        print("Invalid syntax")
        return None
    try:
        x = float(tuple_string[0])
        y = float(tuple_string[1])
        z = float(tuple_string[2])
        player_pos = (x, y, z)
    except ValueError as e:
        print(f"Error on parameter '{tuple_string[e.args[0]]}': could not convert string to float: '{tuple_string[e.args[0]]}'")
        return None
    return player_pos


def calculate_distance(player_pos: tuple, center_pos:
                       tuple) -> float:
    distance_to_center = math.sqrt((player_pos[0] - center_pos[0]) ** 2 +
                                   (player_pos[1] - center_pos[1]) ** 2 +
                                   (player_pos[2] - center_pos[2]) ** 2)
    return distance_to_center


if __name__ == "__main__":
    print("=== Game Coordinate System ===\n")
    print("Get a first set of coordinates")
    player_pos = None
    while player_pos is None:
        player_pos = get_player_pos()
        if player_pos is not None:
            print(f"Got a first tuple: {player_pos}\n"
                  + f"It includes: X={player_pos[0]}, "
                  + f"Y={player_pos[1]}, Z={player_pos[2]}")
            distance = calculate_distance(player_pos, (0, 0, 0))
    print(f"Distance to center: {distance:.4f}")
    print("Get a second set of coordinates")
    other_pos = None
    while other_pos is None:
        other_pos = get_player_pos()
        if other_pos is not None:
            distance = calculate_distance(other_pos, player_pos)
    print(f"Distance between the 2 sets of coordinates: {distance:.4f}")
