#!/usr/bin/env python3
import random


def ft_data_alchemist():
    names_list = ['Alice', 'bob', 'Charlie', 'dylan',
                  'Emma', 'Gregory', 'john', 'kevin', 'Liam']
    print("Initial list of players:", names_list)
    capitalized_list = [name.capitalize() for name in names_list]
    print("New list with all names capitalized: ", capitalized_list)
    only_capitalized = [name for name in names_list if name.istitle()]
    print(f"New list of capitalized names only: {only_capitalized}\n")

    score_dict = {name: random.randint(50, 907) for name in capitalized_list}
    print("Score dict: ", score_dict)
    average_score = round(sum(score_dict.values()) / len(score_dict), 2)
    print("Score average is ", average_score)
    high_scores = {name: score
                   for name, score in score_dict.items()
                   if score > average_score}
    print("High scores: ", high_scores)
