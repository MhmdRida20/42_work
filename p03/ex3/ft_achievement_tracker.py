# !/usr/bin/env python3

import random


# Authorized: len(), print(), import random, random.*, set(), set.union(),
# set.intersection(), set.difference()

def gen_player_achievements():
    achivement_set = {'Crafting Genius', 'Strategist', 'World Savior',
                      'Speed Runner', 'Survivor', 'Master Explorer',
                      'Treasure Hunter', 'Unstoppable', 'First Steps',
                      'Collector Supreme', 'Untouchable', 'Sharp Mind',
                      'Boss Slayer'}
    alice = set()
    bob = set()
    charlie = set()
    dylan = set()

    alice = set(random.sample(list(achivement_set), random.randint(0, len(achivement_set))))
    bob = set(random.sample(list(achivement_set), random.randint(0, len(achivement_set))))
    charlie = set(random.sample(list(achivement_set), random.randint(0, len(achivement_set))))
    dylan = set(random.sample(list(achivement_set), random.randint(0, len(achivement_set))))
    print(f"Player Alice: {alice}")
    print(f"Player Bob: {bob}")
    print(f"Player Charlie: {charlie}")
    print(f"Player Dylan: {dylan}\n")

    #add the untachable achievement to all players
    alice.add('Untouchable')
    bob.add('Untouchable')
    charlie.add('Untouchable')
    dylan.add('Untouchable')

    all_achievements = alice.union(bob).union(charlie).union(dylan)
    print(f"All distinct achievements: {all_achievements}\n")
    
    common_achievements = alice.intersection(bob).intersection(charlie).intersection(dylan)
    print(f"Common achievements: {common_achievements}\n")

    only_alice = alice.difference(bob).difference(charlie).difference(dylan)
    only_bob = bob.difference(alice).difference(charlie).difference(dylan)
    only_charlie = charlie.difference(alice).difference(bob).difference(dylan)
    only_dylan = dylan.difference(alice).difference(bob).difference(charlie).difference(dylan)
    print(f"Only Alice has: {only_alice}")
    print(f"Only Bob has: {only_bob}")
    print(f"Only Charlie has: {only_charlie}")
    print(f"Only Dylan has: {only_dylan}\n")

    missing_alice = achivement_set.difference(alice)
    missing_bob = achivement_set.difference(bob)
    missing_charlie = achivement_set.difference(charlie)
    missing_dylan = achivement_set.difference(dylan)
    print(f"Alice is missing: {missing_alice}")
    print(f"Bob is missing: {missing_bob}")
    print(f"Charlie is missing: {missing_charlie}")
    print(f"Dylan is missing: {missing_dylan}")


def print_achievement_tracker():
    print("=== Achievement Tracker System ===\n")
    gen_player_achievements()


if __name__ == "__main__":
    print_achievement_tracker()