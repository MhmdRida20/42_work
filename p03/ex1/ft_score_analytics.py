#!/usr/bin/env python3

import sys

print("=== Player Score Analytics ===")
checking_list = sys.argv[1:]
if not checking_list or len(checking_list) == 0:
    print("No scores provided. Usage: python3 "
          "ft_score_analytics.py <score1> <score2> ...")
else:
    filtered_list : list = []
    index = 0
    for score in checking_list:
        try:
            score_value = int(score)
            filtered_list.append(score_value)
        except ValueError:
            print(f"Invalid parameter: '{score}'")
    if filtered_list:
        print("Scores Processed: [", end="")
        for s in filtered_list:
            print(f"{s}", end="")
            if s != filtered_list[-1]:
                print(", ", end="")
        print("]")
        total_score = sum(filtered_list)
        average_score = float(total_score / len(filtered_list))
        high_score = max(filtered_list)
        low_score = min(filtered_list)
        score_range = high_score - low_score
        print("Total players: ", len(filtered_list))
        print(f"Total score: {total_score}")
        print(f"Average score: {average_score:.1f}")
        print(f"High score: {high_score}")
        print(f"Low score: {low_score}")
        print(f"Score range: {score_range}")
    else:
        print("No scores provided. Usage: python3"
              " ft_score_analytics.py <score1> <score2> ...")
