# bin/bash/env python3

import sys

print("=== Command Quest ===")
program_name = sys.argv[0]
total_args = len(sys.argv)
if total_args < 2:
    print(f"Program name: {program_name}")
    print("No arguments provided!")
    print(f"Total arguments: {total_args}")
else:
    i = 1
    command = sys.argv[1]
    print(f"Program name: {program_name}")
    print("Arguments received: ", total_args - 1)
    for arg in sys.argv[1:]:
        print(f"Argument {i}: {arg}")
        i += 1
    print(f"Total arguments: {total_args}\n")
