# Lesson Verifier - Spec

## Purpose
A command-line tool that verifies a Hebrew lesson was loaded correctly.
It compares the SOURCE lesson (the oracle: what should be there) with the
LOADED lesson (what the system actually holds) and reports every difference.
It also checks that each exercise is consistent with itself.

## Roles
- Oracle: source.json, the expected lesson content.
- Judge: this tool. It compares loaded.json against source.json.
- Loader / ASR / UI: out of scope. loaded.json is just an export of what
  the system holds.

## Lesson file format (JSON)
A lesson has ordered groups. Each group has one exercise_type and an
ordered list of exercises.

{
  "lesson_id": "L01",
  "groups": [
    {
      "exercise_type": "pronunciation",
      "exercises": [
        {
          "id": "P01",
          "position": 1,
          "target_word": "חָלָב",
          "gloss": "milk",
          "instruction": "Sound it out, then say the whole word.",
          "audio_file": "chalav.mp3"
        }
      ]
    },
    {
      "exercise_type": "build_word",
      "exercises": [
        {
          "id": "B01",
          "position": 1,
          "target_word": "חָלָב",
          "gloss": "milk",
          "image_file": "milk.png",
          "audio_file": "chalav.mp3",
          "beats": [
            { "body": "חָ" },
            { "body": "לָ", "coda": "ב" }
          ],
          "body_tiles": ["בָ", "דִ", "קָ", "לָ", "טָ", "כָ", "חָ"],
          "coda_tiles": ["ן", "ר", "ב", "ג"]
        }
      ]
    }
  ]
}

Terms: a beat is a syllable. Its body is a consonant with its vowel.
Its coda (optional) is the closing consonant. Beats are listed in
reading order.

## Text comparison rule
Hebrew text is normalized (Unicode NFC) on both sides before any
comparison.
- Same word encoded differently (nikud order, presentation forms) = NO issue.
- Different after normalization (a different letter or vowel) = issue.
- Final-form letters (ן ך ם ף ץ) are different from their regular forms.

## Rules
File level
1. MALFORMED_FILE: invalid JSON or a required field is missing
2. DUPLICATE_ID: the same exercise id appears twice in one file

Source vs loaded
3. MISSING_GROUP / EXTRA_GROUP: a group is in one file and not the other
4. WRONG_GROUP_ORDER: same groups, different order
5. MISSING_EXERCISE / EXTRA_EXERCISE: within a group
6. WRONG_ORDER: same exercise, different position
7. WORD_MISMATCH: target_word differs after normalization
8. FIELD_MISMATCH: gloss, instruction, or exercise_type differs
9. ASSET_NAME_MISMATCH: audio_file or image_file name differs
10. TILES_MISMATCH: body_tiles or coda_tiles differ (as sets)

Consistency inside the loaded lesson (build_word)
11. BEATS_DONT_SPELL_WORD: beats joined in order differ from target_word
12. TILE_MISSING: a beat's body or coda is not in its tile list
13. CROSS_GROUP_MISMATCH: the same gloss has different target_words in
    different groups

Optional
14. ASSET_MISSING (only with --assets-dir): a referenced audio or image
    file does not exist

## Output
One line per issue: group, exercise id, rule code, message.
--format json for machine-readable output.
Exit code: 0 = no issues, 1 = issues found, 2 = file or usage error.

## Usage
python verify.py source.json loaded.json [--assets-dir DIR] [--format text|json]

## Out of scope
UI, database, real upload, ASR, AI inside the tool, judging whether the
curriculum is pedagogically correct. Field names are my assumption and
will be adapted to the real system.

## Testing approach
- Every rule has at least one test that triggers it and one that does not.
- Hebrew edge cases: look-alike encodings (must pass), different vowel
  (must fail), final-form letters, mixed Hebrew/English, empty strings.
- Tests are written from this spec, not from the implementation.
- All tests pass locally and on GitHub Actions.

## Definition of done
All rules implemented and tested, CI green, README explains how to run
and includes a short "Working with AI" section: what I asked the agents
to do, and the mistakes I caught.