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
    powerful_mage = max(mages, key=lambda mage: mage.get("power"))
    weakest_mage = min(mages, key=lambda mage: mage.get("power"))
    avg_power = round(sum(lambda mage: mage.get("power"), mages / len(mages)), 2)
    return {
        "max_power": powerful_mage["power"],
        "min_power": weakest_mage["power"],
        "avg_power": avg_power,
    }
