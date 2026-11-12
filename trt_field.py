"""Endliche Körper GF(q) für die Konstruktion der Tischpläne (q Primzahl oder Potenz 4, 8, 9, 16, 25, 27).

Addition und Multiplikation als Tabellen (q ≤ 27 genügt hier): bei Primzahl q Rechnen modulo q, sonst Polynome über GF(p) modulo einem
irreduziblen Polynom (Koeffizienten c0..ck, normiert)."""

_POLY = {
    4: (2, 2, [1, 1, 1]),            # x^2 + x + 1 über GF(2)
    8: (2, 3, [1, 1, 0, 1]),         # x^3 + x + 1 über GF(2)
    9: (3, 2, [1, 0, 1]),            # x^2 + 1 über GF(3)
    16: (2, 4, [1, 1, 0, 0, 1]),     # x^4 + x + 1 über GF(2)
    25: (5, 2, [2, 0, 1]),           # x^2 + 2 über GF(5)
    27: (3, 3, [1, 2, 0, 1]),        # x^3 + 2x + 1 über GF(3)
}


def is_prime(q: int) -> bool:
    return q >= 2 and all(q % d for d in range(2, int(q ** 0.5) + 1))


def is_prime_power(q: int) -> bool:
    """Gibt es einen Körper mit q Elementen, den diese Datei bauen kann (Primzahl oder Eintrag in _POLY)?"""
    return is_prime(q) or q in _POLY


class GF:
    def __init__(self, q: int):
        if not is_prime_power(q):
            raise ValueError(f"Kein Körper mit {q} Elementen verfügbar")
        self.q = q
        if q in _POLY:
            self.p, self.k, self.poly = _POLY[q]
            self.add = [[self._add(a, b) for b in range(q)] for a in range(q)]
            self.mul = [[self._mul(a, b) for b in range(q)] for a in range(q)]
        else:
            self.add = [[(a + b) % q for b in range(q)] for a in range(q)]
            self.mul = [[(a * b) % q for b in range(q)] for a in range(q)]

    def _digits(self, a):
        return [(a // self.p ** i) % self.p for i in range(self.k)]

    def _undig(self, digits):
        return sum(x * self.p ** i for i, x in enumerate(digits))

    def _add(self, a, b):
        return self._undig([(x + y) % self.p for x, y in zip(self._digits(a), self._digits(b))])

    def _mul(self, a, b):
        da, db = self._digits(a), self._digits(b)
        prod = [0] * (2 * self.k - 1)
        for i, x in enumerate(da):
            for j, y in enumerate(db):
                prod[i + j] = (prod[i + j] + x * y) % self.p
        for deg in range(2 * self.k - 2, self.k - 1, -1):
            c = prod[deg]
            if c:
                for i in range(self.k + 1):
                    prod[deg - self.k + i] = (prod[deg - self.k + i] - c * self.poly[i]) % self.p
        return self._undig(prod[: self.k])
