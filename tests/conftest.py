"""Shared helpers for the lesson-verifier tests.

Written from SPEC.md only. The tool is always run as a subprocess.
Hebrew strings are written with \\u escapes so the exact code points are visible.
"""
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VERIFY = ROOT / "verify.py"

RULE_CODES = [
    "MALFORMED_FILE",
    "DUPLICATE_ID",
    "MISSING_GROUP",
    "EXTRA_GROUP",
    "WRONG_GROUP_ORDER",
    "MISSING_EXERCISE",
    "EXTRA_EXERCISE",
    "WRONG_ORDER",
    "WORD_MISMATCH",
    "FIELD_MISMATCH",
    "ASSET_NAME_MISMATCH",
    "TILES_MISMATCH",
    "BEATS_MISMATCH",
    "BEATS_DONT_SPELL_WORD",
    "TILE_MISSING",
    "ASSET_MISSING",
]

# --- Hebrew building blocks (code points spelled out) -----------------------
BET = "ב"
GIMEL = "ג"
DALET = "ד"
HET = "ח"
TET = "ט"
KAF = "כ"
LAMED = "ל"
NUN = "נ"
FINAL_NUN = "ן"
QOF = "ק"
RESH = "ר"
SHIN = "ש"

KAMATS = "ָ"
PATAH = "ַ"
HIRIQ = "ִ"
SEGOL = "ֶ"
DAGESH = "ּ"
SHIN_DOT = "ׁ"

HET_KAMATS = HET + KAMATS            # חָ
LAMED_KAMATS = LAMED + KAMATS        # לָ
CHALAV = HET + KAMATS + LAMED + KAMATS + BET   # חָלָב
CHELAV_SEGOL = HET + SEGOL + LAMED + KAMATS + BET  # חֶלָב (different vowel)

# Look-alike encodings of the same text
BET_DAGESH_PATAH = BET + DAGESH + PATAH   # ב + dagesh + patah
BET_PATAH_DAGESH = BET + PATAH + DAGESH   # ב + patah + dagesh
SHIN_PRECOMPOSED = "שׁ"               # שׁ as one character
SHIN_DECOMPOSED = SHIN + SHIN_DOT         # ש + shin dot


def valid_lesson():
    """The spec's JSON example, as a fresh dict. The tool must accept it."""
    return {
        "lesson_id": "L01",
        "groups": [
            {
                "group_id": "G1",
                "exercise_type": "pronunciation",
                "exercises": [
                    {
                        "id": "P01",
                        "position": 1,
                        "target_word": CHALAV,
                        "translation": "milk",
                        "instruction": "Sound it out, then say the whole word.",
                        "audio_file": "chalav.mp3",
                    }
                ],
            },
            {
                "group_id": "G2",
                "exercise_type": "build_word",
                "exercises": [
                    {
                        "id": "B01",
                        "position": 1,
                        "target_word": CHALAV,
                        "translation": "milk",
                        "image_file": "milk.png",
                        "audio_file": "chalav.mp3",
                        "beats": [
                            {"body": HET_KAMATS},
                            {"body": LAMED_KAMATS, "coda": BET},
                        ],
                        "body_tiles": [
                            BET + KAMATS,
                            DALET + HIRIQ,
                            QOF + KAMATS,
                            LAMED_KAMATS,
                            TET + KAMATS,
                            KAF + KAMATS,
                            HET_KAMATS,
                        ],
                        "coda_tiles": [FINAL_NUN, RESH, BET, GIMEL],
                    }
                ],
            },
        ],
    }


def pron_exercise(ex_id, position, word=CHALAV, translation="milk"):
    return {
        "id": ex_id,
        "position": position,
        "target_word": word,
        "translation": translation,
        "instruction": "Sound it out, then say the whole word.",
        "audio_file": "chalav.mp3",
    }


def get_group(lesson, group_id):
    return next(g for g in lesson["groups"] if g["group_id"] == group_id)


def get_ex(lesson, group_id, ex_id):
    return next(e for e in get_group(lesson, group_id)["exercises"] if e["id"] == ex_id)


def three_group_lesson():
    """Valid lesson with a third group (pronunciation G3 / P03)."""
    lesson = valid_lesson()
    lesson["groups"].append(
        {
            "group_id": "G3",
            "exercise_type": "pronunciation",
            "exercises": [pron_exercise("P03", 1)],
        }
    )
    return lesson


def two_exercise_lesson():
    """Valid lesson whose G1 has two exercises (P01 pos 1, P02 pos 2)."""
    lesson = valid_lesson()
    get_group(lesson, "G1")["exercises"].append(pron_exercise("P02", 2, translation="water"))
    return lesson


# --- Running the tool -------------------------------------------------------
class Result:
    def __init__(self, completed):
        self.returncode = completed.returncode
        self.stdout = completed.stdout.decode("utf-8", errors="replace")
        self.stderr = completed.stderr.decode("utf-8", errors="replace")

    @property
    def lines(self):
        return [ln for ln in self.stdout.splitlines() if ln.strip()]

    @property
    def codes(self):
        """Set of rule codes that appear in stdout (as whole tokens)."""
        return {
            c
            for c in RULE_CODES
            if re.search(rf"(?<![A-Z_]){c}(?![A-Z_])", self.stdout)
        }

    def lines_with(self, code):
        return [ln for ln in self.lines if re.search(rf"(?<![A-Z_]){code}(?![A-Z_])", ln)]


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_cli(*args, cwd=None):
    completed = subprocess.run(
        [sys.executable, str(VERIFY), *map(str, args)],
        capture_output=True,
        cwd=cwd,
        timeout=60,
    )
    return Result(completed)


@pytest.fixture
def verify(tmp_path):
    """verify(source_dict, loaded_dict, *extra_args) -> Result.

    Writes source.json / loaded.json (UTF-8, ensure_ascii=False) into tmp_path.
    """

    def _verify(source, loaded, *extra_args):
        src = write_json(tmp_path / "source.json", source)
        ld = write_json(tmp_path / "loaded.json", loaded)
        return run_cli(src, ld, *extra_args, cwd=tmp_path)

    return _verify


@pytest.fixture
def assets_dir(tmp_path):
    """An assets directory holding every asset the valid lesson names."""
    d = tmp_path / "assets"
    d.mkdir()
    (d / "chalav.mp3").write_bytes(b"x")
    (d / "milk.png").write_bytes(b"x")
    return d


@pytest.fixture
def run_files(tmp_path):
    """run_files(source_path, loaded_path, *extra) for tests that craft raw files."""

    def _run(source_path, loaded_path, *extra_args):
        return run_cli(source_path, loaded_path, *extra_args, cwd=tmp_path)

    return _run


@pytest.fixture
def good_file(tmp_path):
    """Path of a valid lesson file, to pair with a broken one."""
    return write_json(tmp_path / "good.json", valid_lesson())


def clone(obj):
    return copy.deepcopy(obj)
