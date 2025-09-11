# Test Plan
1) Parsing: parse_date/parse_number + schema (positions/transactions).
2) Contributions: teckenlogik (Insättning+/Uttag−) och månadssummering.
3) MWRR: konvergens med bounds + numerisk fallback.
4) Monte Carlo: determinism med fast seed; rimliga percentiler.
5) E2E-smoke: genererar båda CSV i result/ och skriver logs/app.log.
6) Validering: saknade/extra kolumner → tydligt felmeddelande.
