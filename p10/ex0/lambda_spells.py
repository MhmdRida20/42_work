def artifact_sorter(artifacts: list[dict]) -> list[dict]:
    return sorted(artifacts,
                  key=lambda artifact: artifact.get("power", 0), reverse=True)


def power_filter(mages: list[dict], min_power: int) -> list[dict]:
    return list(filter(lambda mage: mage.get("power", 0) >= min_power, mages))


def spell_transformer(spells: list[str]) -> list[str]:
    return list(map(lambda spell: spell.upper(), spells))


def mage_stats(mages: list[dict]) -> dict:
    if not mages:
        return {"max_power": 0, "min_power": 0, "avg_power": 0.0}
    powerful_mage = max(mages, key=lambda mage: mage["power"])
    weakest_mage = min(mages, key=lambda mage: mage["power"])
    avg_power = round(sum(map(lambda mage: mage["power"], mages)) / len(mages),
                      2)
    return {
        "max_power": powerful_mage["power"],
        "min_power": weakest_mage["power"],
        "avg_power": avg_power,
    }


def main():
    print("Testing artifact sorter...")
    artifacts = [
        {'name': 'Fire Staff', 'power': 92, 'type': 'weapon'},
        {'name': 'Crystal Orb', 'power': 85, 'type': 'focus'},
        {'name': 'Ice Wand', 'power': 78, 'type': 'weapon'},
        {'name': 'Storm Crown', 'power': 105, 'type': 'relic'},
    ]
    sorted_artifacts = artifact_sorter(artifacts)
    a, b = sorted_artifacts[0], sorted_artifacts[1]
    print(f"{a['name']} ({a['power']} power) comes before "
          f"{b['name']} ({b['power']} power)")

    print("\nTesting power filter...")
    mages = [
        {'name': 'Alex', 'power': 88, 'element': 'fire'},
        {'name': 'Riley', 'power': 65, 'element': 'ice'},
        {'name': 'Sage', 'power': 72, 'element': 'wind'},
        {'name': 'Nova', 'power': 91, 'element': 'shadow'},
    ]
    filtered = power_filter(mages, 70)
    print(f"Mages with power >= 70: {[m['name'] for m in filtered]}")

    print("\nTesting spell transformer...")
    spells = ["fireball", "heal", "shield"]
    print(" ".join(spell_transformer(spells)))

    print("\nTesting mage stats...")
    print(mage_stats(mages))


if __name__ == "__main__":
    main()
