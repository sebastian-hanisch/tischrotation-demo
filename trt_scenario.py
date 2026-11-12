"""Szenario: Firmenfeier mit s Abteilungen à m Personen. Beschriftungen der Personen und Abteilungen; die Instanz hängt nur an (s, m)."""

from dataclasses import dataclass

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass(frozen=True)
class Party:
    s: int  # Abteilungen = Personen an jedem Tisch
    m: int  # Personen je Abteilung = Tische je Runde

    @property
    def n(self) -> int:
        return self.s * self.m

    def dept(self, p: int) -> int:
        return p // self.m

    def label(self, p: int) -> str:
        """Beschriftung: Abteilungsbuchstabe und Nummer, z. B. A1 (Person 0), B3 (Abteilung B, dritte Person)."""
        return f"{LETTERS[p // self.m]}{p % self.m + 1}"

    def cross_pairs(self) -> int:
        """Paare aus verschiedenen Abteilungen."""
        return self.n * (self.n - 1) // 2 - self.s * (self.m * (self.m - 1) // 2)
