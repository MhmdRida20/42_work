#!/usr/bin/env python3
"""Validate alien contact reports with Pydantic v2."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ValidationError, model_validator


class ContactType(str, Enum):
    """Supported types of alien contact."""

    RADIO = "radio"
    VISUAL = "visual"
    PHYSICAL = "physical"
    TELEPATHIC = "telepathic"


class AlienContact(BaseModel):
    """Represent and validate an alien contact report."""

    contact_id: str = Field(min_length=5, max_length=15)
    timestamp: datetime
    location: str = Field(min_length=3, max_length=100)
    contact_type: ContactType
    signal_strength: float = Field(ge=0.0, le=10.0)
    duration_minutes: int = Field(ge=1, le=1440)
    witness_count: int = Field(ge=1, le=100)
    message_received: str | None = Field(default=None, max_length=500)
    is_verified: bool = False

    @model_validator(mode="after")
    def validate_contact_rules(self) -> AlienContact:
        """Apply business rules involving multiple fields."""
        if not self.contact_id.startswith("AC"):
            raise ValueError("Contact ID must start with 'AC'")

        if (
            self.contact_type == ContactType.PHYSICAL
            and not self.is_verified
        ):
            raise ValueError("Physical contact reports must be verified")

        if (
            self.contact_type == ContactType.TELEPATHIC
            and self.witness_count < 3
        ):
            raise ValueError(
                "Telepathic contact requires at least 3 witnesses"
            )

        if self.signal_strength > 7.0 and not self.message_received:
            raise ValueError(
                "Strong signals must include a received message"
            )

        return self


def display_contact(contact: AlienContact) -> None:
    """Display a validated alien contact report."""
    print(f"ID: {contact.contact_id}")
    print(f"Type: {contact.contact_type.value}")
    print(f"Location: {contact.location}")
    print(f"Time: {contact.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Signal: {contact.signal_strength}/10")
    print(f"Duration: {contact.duration_minutes} minutes")
    print(f"Witnesses: {contact.witness_count}")

    if contact.message_received is not None:
        print(f"Message: '{contact.message_received}'")
    else:
        print("Message: None")

    verification = "Verified" if contact.is_verified else "Unverified"
    print(f"Verification: {verification}")


def show_first_validation_error(error: ValidationError) -> None:
    """Print the first clear validation message."""
    errors = error.errors()

    if errors:
        print(errors[0]["msg"])
    else:
        print(str(error))


def main() -> None:
    """Demonstrate valid and invalid alien contact reports."""
    print("Alien Contact Log Validation")
    print("=" * 38)

    valid_contact_data: dict[str, object] = {
        "contact_id": "AC_2024_001",
        "timestamp": "2024-01-15T14:30:00",
        "location": "Area 51, Nevada",
        "contact_type": "radio",
        "signal_strength": 8.5,
        "duration_minutes": 45,
        "witness_count": 5,
        "message_received": "Greetings from Zeta Reticuli",
        "is_verified": True,
    }

    try:
        contact = AlienContact.model_validate(valid_contact_data)
        print("Valid contact report:")
        display_contact(contact)
    except ValidationError as error:
        print("Unexpected validation error:")
        print(error)

    print("=" * 38)

    invalid_contact_data: dict[str, object] = {
        "contact_id": "AC_2024_002",
        "timestamp": "2024-01-16T09:15:00",
        "location": "Roswell, New Mexico",
        "contact_type": "telepathic",
        "signal_strength": 6.2,
        "duration_minutes": 30,
        "witness_count": 1,
        "message_received": None,
        "is_verified": False,
    }

    try:
        AlienContact.model_validate(invalid_contact_data)
    except ValidationError as error:
        print("Expected validation error:")
        show_first_validation_error(error)


if __name__ == "__main__":
    main()
