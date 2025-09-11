
def parse_number(s: str) -> float:
    """Enkel Avanza-parser: ta bort mellanslag och byter kommatecken till punkt."""
    return float(
        s.strip()
         .replace(" ", "")
         .replace(",", ".")
    )
