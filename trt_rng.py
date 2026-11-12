"""Eigener Zufallsgenerator (SplitMix64): gleiche Zufalls-Seeds geben auf jeder Python-Version und Plattform dieselben Folgen.

Python-`random` ist für feste Zufalls-Seeds über Versionen hinweg nicht zugesichert; die Messreihen der README hängen an diesen Folgen."""

MASK = (1 << 64) - 1


class SplitMix64:
    def __init__(self, seed: int):
        self.state = seed & MASK

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def random(self) -> float:
        """Gleichverteilt in [0, 1) mit 53 Bit."""
        return (self.next_u64() >> 11) / float(1 << 53)

    def below(self, n: int) -> int:
        """Ganzzahl in 0..n-1 (Rest der Division; der Fehler 2^-64 · n ist hier ohne Belang)."""
        return self.next_u64() % n

    def shuffle(self, items: list) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = self.below(i + 1)
            items[i], items[j] = items[j], items[i]
