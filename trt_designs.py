"""Konstruktionen: Körper-Konstruktion und Auffüllen und Streichen.

Abteilungsmischung: s Abteilungen mit je m Personen, Person p = d·m + i (Abteilung d, Nummer i). An jedem Tisch sitzt höchstens eine Person je Abteilung.
Ein Plan ist eine Liste von Runden, eine Runde eine Liste von Tischen, ein Tisch eine Liste von Personen."""

from trt_field import GF, is_prime_power


def next_prime_power(x: int) -> int:
    """Kleinste Zahl q ≥ x, für die ein Körper mit q Elementen verfügbar ist."""
    q = max(2, x)
    while not is_prime_power(q):
        q += 1
    return q


def transversal_rounds(s: int, q: int) -> list:
    """q Runden mit q Tischen für s Abteilungen à q Personen (q Körpergröße, s ≤ q): Person i der Abteilung d sitzt in Runde r an Tisch t, wenn i = t + r·d im Körper.

    Jedes Paar aus verschiedenen Abteilungen sitzt genau einmal an einem Tisch, kein Paar derselben Abteilung."""
    if s > q:
        raise ValueError("Mehr Abteilungen als Körperelemente")
    field = GF(q)
    return [[[d * q + field.add[t][field.mul[r][d]] for d in range(s)] for t in range(q)] for r in range(q)]


def construction_available(s: int, m: int) -> bool:
    """Körper-Konstruktion mit genau m Tischen à s Personen: m Primzahlpotenz und höchstens m Abteilungen."""
    return is_prime_power(m) and s <= m


def construction_plan(s: int, m: int) -> list:
    if not construction_available(s, m):
        raise ValueError("Keine Körper-Konstruktion für diese Größe")
    return transversal_rounds(s, m)


def fill_plan(s: int, m: int) -> tuple:
    """Auffüllen und Streichen: q = kleinste Primzahlpotenz ≥ max(m, s); Konstruktion für q Personen je Abteilung; in jeder Abteilung die Personen mit Nummer ≥ m streichen.

    Ergebnis (q, Plan): q Runden ohne Wiederholung mit bis zu q Tischen je Runde; Tische mit bis zu q − m Personen weniger als s (bei m = q gibt es keine)."""
    q = next_prime_power(max(m, s))
    plan = []
    for rnd in transversal_rounds(s, q):
        tables = []
        for table in rnd:
            kept = [(p // q) * m + (p % q) for p in table if p % q < m]
            if kept:
                tables.append(kept)
        plan.append(tables)
    return q, plan
