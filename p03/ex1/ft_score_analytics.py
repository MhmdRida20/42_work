# bin/bash/env python3

import sys

print("=== Player Score Analytics ===")
cheking_list = sys.argv[1:]
if not cheking_list or len(cheking_list) == 0:
    print("No scores provided. Usage: python3 "
          "ft_score_analytics.py <score1> <score2> ...")
