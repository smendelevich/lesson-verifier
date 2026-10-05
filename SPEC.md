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
Files are UTF-8 encoded. The tool reads them as UTF-8.
A lesson has ordered groups. Each group has one exercise_type and an
ordered list of exercises.

```json
{
  "lesson_id": "L01",
  "groups": [
    {
      "group_id": "G1",
      "exercise_type": "pronunciation",
      "exercises": [
        {
          "id": "P01",
          "position": 1,
          "target_word": "חָלָב",
          "translation": "milk",
          "instruction": "Sound it out, then say the whole word.",
          "audio_file": "chalav.mp3"
        }
      ]
    },
    {
      "group_id": "G2",
      "exercise_type": "build_word",
      "exercises": [
        {
          "id": "B01",
          "position": 1,
          "target_word": "חָלָב",
          "translation": "milk",
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
```
Terms: a beat is a syllable. Its body is a consonant with its vowel.
Its coda (optional) is the closing consonant. Beats are listed in
reading order.

## Required fields
- Lesson: lesson_id, groups
- Group: group_id, exercise_type, exercises
- Exercise, type pronunciation: id, position, target_word,
  translation, instruction, audio_file
- Exercise, type build_word: id, position, target_word, translation,
  image_file, audio_file, beats, body_tiles, coda_tiles
- Beat: body (coda is optional)


## Background: Hebrew text and look-alike encodings

In Hebrew with nikud (vowel marks), a letter and its marks are SEPARATE
characters in the file. For example, בַּ is stored as three characters:
ב (U+05D1) + dagesh (U+05BC) + patah (U+05B7).

Because marks are separate characters, the same word can be stored in
more than one way, and the versions look identical on screen:

1. Different mark order:
   ב + dagesh + patah   vs   ב + patah + dagesh
2. Single-character form vs. letter + mark:
   שׁ as one character (U+FB2A)   vs   ש (U+05E9) + shin dot (U+05C1)

These are "look-alike encodings". A plain string comparison says they
are different. For a lesson, they ARE the same word, so reporting them
would be a false alarm.

Unicode NFC normalization converts all such versions to one standard
form. The tool normalizes both sides with NFC before any comparison.

NFC does NOT hide real differences:
- A different vowel (חָלָב vs חֶלָב) is still different after NFC.
- Final-form letters (ן ך ם ף ץ) are different characters from their
  regular forms (נ כ מ פ צ). NFC does not merge them.

Note for readers who don't know Hebrew: you cannot tell look-alike
encodings apart visually. Always compare the characters (code points),
not the rendered text.

## Text comparison rule
Normalize Hebrew text (NFC) on both sides before any comparison.
See "Background: Hebrew text and look-alike encodings".
- Look-alike encodings of the same word: verifier reports NO issue.
- A different letter or vowel: verifier reports WORD_MISMATCH.

## Matching
- Groups are matched by group_id. Exercises are matched by id within
  the matched group.
- A group_id or an exercise id that appears more than once in one file is DUPLICATE_ID.
- Group order is the order in the groups list. Exercise order is the
  position field (WRONG_ORDER if positions differ).

## Comparing
- For each matched pair (group or exercise), every field is compared.
- Hebrew text fields (target_word, beats.body, beats.coda, body_tiles, coda_tiles) 
  are compared after NFC normalization; other text (such as translation)
  is compared as is.
- Lists of tiles are compared as sets; beats are compared in order.
- A field that has no specific rule below is reported as FIELD_MISMATCH.

## Rules
#### File level:
1. MALFORMED_FILE: a required field is missing, or exercise_type is unknown
2. DUPLICATE_ID: the same exercise id or group id appears more than once in one file

#### Source vs loaded:
3. MISSING_GROUP / EXTRA_GROUP: a group is in one file and not the other
4. WRONG_GROUP_ORDER: same groups, different order
5. MISSING_EXERCISE / EXTRA_EXERCISE: within a group
6. WRONG_ORDER: same exercise, different position
7. WORD_MISMATCH: target_word differs after normalization
8. FIELD_MISMATCH: any other field differs, for example translation, instruction, exercise_type.
9. ASSET_NAME_MISMATCH: audio_file or image_file name differs
10. TILES_MISMATCH: body_tiles or coda_tiles differ (as sets)
11. BEATS_MISMATCH: beats differ between source and loaded (in order)

#### Consistency inside the loaded lesson (checked on the loaded file only) (build_word):
12. BEATS_DONT_SPELL_WORD: the beats joined in order (for each beat,
    body then coda) differ from target_word after NFC normalization.
13. TILE_MISSING: a beat's body or coda is not in its tile list

#### Optional:
14. ASSET_MISSING (only with --assets-dir, loaded file only): an
    audio_file or image_file named in the loaded lesson does not exist
    in the assets directory. Names are looked up directly in that
    directory, not in subfolders.

## Output
- One line per issue: file, group id, exercise id, rule code, message.
- file is source or loaded. For source vs loaded issues, file is loaded.
- Group id and exercise id are empty when they don't apply or are
  unknown (for example MISSING_GROUP has no exercise id; a missing id
  can't be printed).
- --format json for machine-readable output.
- Hebrew must stay readable in the output (text and JSON), not escaped
  or garbled.
- Issues are printed to stdout. Error messages (exit code 2) go to stderr.
- Exit code: 0 = no issues, 1 = issues found, 2 = file or usage error.

## Errors
- File missing, unreadable, or not valid JSON: print an error, exit 2.
- Valid JSON with a missing required field: report MALFORMED_FILE and
  say where in the message (for example "groups[0].exercises[1]: missing
  target_word"). Exit 1.
- If either file has MALFORMED_FILE or DUPLICATE_ID issues, report them
  and skip all other checks, because checking broken data gives
  unreliable results.
- An exercise_type other than pronunciation or build_word:
  report MALFORMED_FILE ("unknown exercise_type").

## Usage
python verify.py source.json loaded.json [--assets-dir DIR] [--format text|json]

## Out of scope
UI, database, real upload, ASR, AI inside the tool, judging whether the
curriculum is pedagogically correct. Field names are my assumption and
will be adapted to the real system.

## Testing approach
- Every rule has at least one test that triggers it and one that does not.
- Hebrew edge cases: look-alike encodings (NO issue reported), different vowel
  (WORD_MISMATCH reported), final-form letters, mixed Hebrew/English, empty strings.
- All tests pass locally and on GitHub Actions.

## Definition of done
All rules implemented and tested, CI green, README explains how to run
and includes a short "Working with AI" section: what I asked the agents
to do, and the mistakes I caught.