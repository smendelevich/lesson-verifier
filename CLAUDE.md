# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Python CLI tool (`verify.py`) that compares two Hebrew lesson JSON files — `source.json` (the oracle) and `loaded.json` (what the system holds) — and reports every difference using a fixed set of rule codes. See SPEC.md for the full spec.

## Commands

```bash
# Run the tool
python verify.py source.json loaded.json [--assets-dir DIR] [--format text|json]

# Run all tests
pytest

# Run a single test
pytest tests/test_rules.py::test_word_mismatch
```

Exit codes: `0` no issues, `1` issues found, `2` file/usage error.

## Key constraints

**Hebrew text comparison:** Always NFC-normalize both sides before comparing. Look-alike encodings that normalize to the same form are not issues. Final-form letters (ן ך ם ף ץ) are distinct from their base forms.

**Rule codes** (14 total, defined in SPEC.md): `MALFORMED_FILE`, `DUPLICATE_ID`, `MISSING_GROUP`, `EXTRA_GROUP`, `WRONG_GROUP_ORDER`, `MISSING_EXERCISE`, `EXTRA_EXERCISE`, `WRONG_ORDER`, `WORD_MISMATCH`, `FIELD_MISMATCH`, `ASSET_NAME_MISMATCH`, `TILES_MISMATCH`, `BEATS_DONT_SPELL_WORD`, `TILE_MISSING`, `CROSS_GROUP_MISMATCH`, `ASSET_MISSING`.

**TILES_MISMATCH** compares tile lists as sets (order doesn't matter). **CROSS_GROUP_MISMATCH** checks that the same gloss always maps to the same `target_word` across all groups.

## Testing requirements

Every rule needs at least one test that triggers it and one that does not. Required Hebrew edge cases: look-alike encodings with different nikud order (must **pass**), different vowel/letter after NFC (must **fail**), final-form letters, mixed Hebrew/English, empty strings. Tests are written from the spec, not the implementation.
