from typing import NewType

SECONDS = NewType("SECONDS", int)
MINUTES = NewType("MINUTES", int)
HOURS = NewType("HOURS", int)
DAYS = NewType("DAYS", int)
WEEKS = NewType("WEEKS", int)
MONTHS = NewType("MONTHS", int)
YEARS = NewType("YEARS", int)

__all__ = ["SECONDS", "MINUTES", "HOURS", "DAYS", "WEEKS", "MONTHS", "YEARS"]
