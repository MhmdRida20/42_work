#!/usr/bin/env python3
"""Validate space-station data with Pydantic v2."""

from datetime import datetime

from pydantic import BaseModel, Field, ValidationError


class SpaceStation(BaseModel):
    """Represent and validate a monitored space station."""

    station_id: str = Field(min_length=3, max_length=10)
    name: str = Field(min_length=1, max_length=50)
    crew_size: int = Field(ge=1, le=20)
    power_level: float = Field(ge=0.0, le=100.0)
    oxygen_level: float = Field(ge=0.0, le=100.0)
    last_maintenance: datetime
    is_operational: bool = True
    notes: str | None = Field(default=None, max_length=200)


def display_station(station: SpaceStation) -> None:
    """Display validated station information in a readable format."""
    status = "Operational" if station.is_operational else "Not operational"

    print(f"ID: {station.station_id}")
    print(f"Name: {station.name}")
    print(f"Crew: {station.crew_size} people")
    print(f"Power: {station.power_level}%")
    print(f"Oxygen: {station.oxygen_level}%")
    print(
        "Last maintenance: "
        f"{station.last_maintenance.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print(f"Status: {status}")

    if station.notes is not None:
        print(f"Notes: {station.notes}")


def show_first_validation_error(error: ValidationError) -> None:
    """Print the first clear validation message from a Pydantic error."""
    errors = error.errors()
    if errors:
        print(errors[0]["msg"])
    else:
        print(str(error))


def main() -> None:
    """Demonstrate successful and failed space-station validation."""
    print("Space Station Data Validation")
    print("=" * 40)

    valid_station_data: dict[str, object] = {
        "station_id": "ISS001",
        "name": "International Space Station",
        "crew_size": 6,
        "power_level": 85.5,
        "oxygen_level": 92.3,
        "last_maintenance": "2024-01-15T10:30:00",
        "notes": "All systems nominal",
    }

    try:
        station = SpaceStation.model_validate(valid_station_data)
        print("Valid station created:")
        display_station(station)
    except ValidationError as error:
        print("Unexpected validation error:")
        print(error)

    print("=" * 40)

    invalid_station_data: dict[str, object] = {
        "station_id": "MARS01",
        "name": "Mars Research Station",
        "crew_size": 25,
        "power_level": 90.0,
        "oxygen_level": 95.0,
        "last_maintenance": "2024-02-01T08:00:00",
    }

    try:
        SpaceStation.model_validate(invalid_station_data)
    except ValidationError as error:
        print("Expected validation error:")
        show_first_validation_error(error)


if __name__ == "__main__":
    main()
