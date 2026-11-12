"""Gemeinsame Fixtures: Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini_plan():
    """Drei Abteilungen zu je 2 Personen (Personen 0,1 | 2,3 | 4,5). Handrechnung (aus dem Körper GF(3) gebildet, i = t + r·d, Personen mit i = 2 gestrichen):
    Runde 1: {0,2,4} {1,3,5}; Runde 2: {0,3} {1,4} {2,5}; Runde 3: {0,5} {1,2} {3,4}. Alle 12 Paare aus verschiedenen Abteilungen genau einmal."""
    return [[[0, 2, 4], [1, 3, 5]], [[0, 3], [1, 4], [2, 5]], [[0, 5], [1, 2], [3, 4]]]
