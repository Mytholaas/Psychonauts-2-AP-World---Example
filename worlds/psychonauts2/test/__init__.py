"""
Psychonauts 2 Archipelago - Test Suite

Provides a shared test base class and imports for world-specific tests.
"""

from test.bases import WorldTestBase


class Psy2TestBase(WorldTestBase):
    """Base class for all Psychonauts 2 Archipelago tests."""
    game = "Psychonauts 2"
