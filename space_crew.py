#!/usr/bin/env python3
"""Validate space crews and missions with Pydantic v2."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ValidationError, model_validator


class Rank(str, Enum):
    """Supported crew ranks."""

    CADET = "cadet"
    OFFICER = "officer"
    LIEUTENANT = "lieutenant"
    CAPTAIN = "captain"
    COMMANDER = "commander"


class CrewMember(BaseModel):
    """Represent and validate one crew member."""

    member_id: str = Field(min_length=3, max_length=10)
    name: str = Field(min_length=2, max_length=50)
    rank: Rank
    age: int = Field(ge=18, le=80)
    specialization: str = Field(min_length=3, max_length=30)
    years_experience: int = Field(ge=0, le=50)
    is_active: bool = True


class SpaceMission(BaseModel):
    """Represent and validate a space mission and its crew."""

    mission_id: str = Field(min_length=5, max_length=15)
    mission_name: str = Field(min_length=3, max_length=100)
    destination: str = Field(min_length=3, max_length=50)
    launch_date: datetime
    duration_days: int = Field(ge=1, le=3650)
    crew: list[CrewMember] = Field(min_length=1, max_length=12)
    mission_status: str = "planned"
    budget_millions: float = Field(ge=1.0, le=10000.0)

    @model_validator(mode="after")
    def validate_mission_rules(self) -> SpaceMission:
        """Apply mission safety rules involving the entire crew."""
        if not self.mission_id.startswith("M"):
            raise ValueError("Mission ID must start with 'M'")

        has_leader = any(
            member.rank in {Rank.COMMANDER, Rank.CAPTAIN}
            for member in self.crew
        )
        if not has_leader:
            raise ValueError(
                "Mission must have at least one Commander or Captain"
            )

        if self.duration_days > 365:
            experienced_count = sum(
                member.years_experience >= 5 for member in self.crew
            )
            required_experienced = (len(self.crew) + 1) // 2

            if experienced_count < required_experienced:
                raise ValueError(
                    "Long missions require at least 50% experienced crew"
                )

        if any(not member.is_active for member in self.crew):
            raise ValueError("All crew members must be active")

        return self


def display_mission(mission: SpaceMission) -> None:
    """Display a validated space mission and its crew."""
    print(f"Mission: {mission.mission_name}")
    print(f"ID: {mission.mission_id}")
    print(f"Destination: {mission.destination}")
    print(f"Launch: {mission.launch_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {mission.duration_days} days")
    print(f"Budget: ${mission.budget_millions}M")
    print(f"Status: {mission.mission_status}")
    print(f"Crew size: {len(mission.crew)}")
    print("Crew members:")

    for member in mission.crew:
        print(
            f"- {member.name} ({member.rank.value}) - "
            f"{member.specialization}"
        )


def show_first_validation_error(error: ValidationError) -> None:
    """Print the first clear validation message."""
    errors = error.errors()

    if errors:
        print(errors[0]["msg"])
    else:
        print(str(error))


def main() -> None:
    """Demonstrate valid and invalid nested mission validation."""
    print("Space Mission Crew Validation")
    print("=" * 41)

    valid_mission_data: dict[str, object] = {
        "mission_id": "M2024_MARS",
        "mission_name": "Mars Colony Establishment",
        "destination": "Mars",
        "launch_date": "2024-09-01T08:00:00",
        "duration_days": 900,
        "budget_millions": 2500.0,
        "crew": [
            {
                "member_id": "CM001",
                "name": "Sarah Connor",
                "rank": "commander",
                "age": 48,
                "specialization": "Mission Command",
                "years_experience": 20,
                "is_active": True,
            },
            {
                "member_id": "CM002",
                "name": "John Smith",
                "rank": "lieutenant",
                "age": 36,
                "specialization": "Navigation",
                "years_experience": 10,
                "is_active": True,
            },
            {
                "member_id": "CM003",
                "name": "Alice Johnson",
                "rank": "officer",
                "age": 29,
                "specialization": "Engineering",
                "years_experience": 3,
                "is_active": True,
            },
        ],
    }

    try:
        mission = SpaceMission.model_validate(valid_mission_data)
        print("Valid mission created:")
        display_mission(mission)
    except ValidationError as error:
        print("Unexpected validation error:")
        print(error)

    print("=" * 41)

    invalid_mission_data: dict[str, object] = {
        "mission_id": "M2024_LUNA",
        "mission_name": "Lunar Research Mission",
        "destination": "Moon",
        "launch_date": "2024-06-15T12:00:00",
        "duration_days": 180,
        "budget_millions": 800.0,
        "crew": [
            {
                "member_id": "CM010",
                "name": "David Miller",
                "rank": "officer",
                "age": 34,
                "specialization": "Research",
                "years_experience": 8,
                "is_active": True,
            },
            {
                "member_id": "CM011",
                "name": "Emma Brown",
                "rank": "lieutenant",
                "age": 31,
                "specialization": "Medical Officer",
                "years_experience": 6,
                "is_active": True,
            },
        ],
    }

    try:
        SpaceMission.model_validate(invalid_mission_data)
    except ValidationError as error:
        print("Expected validation error:")
        show_first_validation_error(error)


if __name__ == "__main__":
    main()
