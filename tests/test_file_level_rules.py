"""Rules 1-2 (MALFORMED_FILE, DUPLICATE_ID) and the skip-all-other-checks behavior."""
import pytest

from conftest import (
    BET, CHALAV, clone, get_ex, get_group, pron_exercise, valid_lesson,
)

FILE_LEVEL = {"MALFORMED_FILE", "DUPLICATE_ID"}


# --- Rule 1: MALFORMED_FILE -------------------------------------------------
def test_valid_lesson_has_no_issues(verify):
    result = verify(valid_lesson(), valid_lesson())
    assert result.returncode == 0
    assert result.codes == set()


def test_missing_lesson_id_is_malformed(verify):
    bad = valid_lesson()
    del bad["lesson_id"]
    result = verify(valid_lesson(), bad)
    assert result.returncode == 1
    assert "MALFORMED_FILE" in result.codes


def test_missing_groups_is_malformed(verify):
    bad = valid_lesson()
    del bad["groups"]
    result = verify(valid_lesson(), bad)
    assert result.returncode == 1
    assert "MALFORMED_FILE" in result.codes


@pytest.mark.parametrize("field", ["group_id", "exercise_type", "exercises"])
def test_missing_group_field_is_malformed(verify, field):
    bad = valid_lesson()
    del bad["groups"][0][field]
    result = verify(valid_lesson(), bad)
    assert result.returncode == 1
    assert "MALFORMED_FILE" in result.codes


@pytest.mark.parametrize(
    "field",
    ["id", "position", "target_word", "translation", "instruction", "audio_file"],
)
def test_missing_pronunciation_field_is_malformed(verify, field):
    bad = valid_lesson()
    del get_ex(bad, "G1", "P01")[field]
    result = verify(valid_lesson(), bad)
    assert result.returncode == 1
    assert "MALFORMED_FILE" in result.codes


@pytest.mark.parametrize(
    "field",
    [
        "id", "position", "target_word", "translation", "image_file",
        "audio_file", "beats", "body_tiles", "coda_tiles",
    ],
)
def test_missing_build_word_field_is_malformed(verify, field):
    bad = valid_lesson()
    del get_ex(bad, "G2", "B01")[field]
    result = verify(valid_lesson(), bad)
    assert result.returncode == 1
    assert "MALFORMED_FILE" in result.codes


def test_beat_without_body_is_malformed(verify):
    bad = valid_lesson()
    del get_ex(bad, "G2", "B01")["beats"][0]["body"]
    result = verify(valid_lesson(), bad)
    assert result.returncode == 1
    assert "MALFORMED_FILE" in result.codes


def test_unknown_exercise_type_is_malformed(verify):
    bad = valid_lesson()
    get_group(bad, "G1")["exercise_type"] = "listening"
    result = verify(valid_lesson(), bad)
    assert result.returncode == 1
    assert "MALFORMED_FILE" in result.codes
    assert "unknown exercise_type" in result.stdout


def test_malformed_message_says_where(verify):
    bad = valid_lesson()
    del get_ex(bad, "G1", "P01")["target_word"]
    result = verify(valid_lesson(), bad)
    line = result.lines_with("MALFORMED_FILE")[0]
    assert "groups[0].exercises[0]" in line
    assert "target_word" in line


def test_malformed_in_source_is_reported_with_file_source(verify):
    bad = valid_lesson()
    del get_ex(bad, "G1", "P01")["translation"]
    result = verify(bad, valid_lesson())
    line = result.lines_with("MALFORMED_FILE")[0]
    assert "source" in line
    assert "loaded" not in line


def test_malformed_in_loaded_is_reported_with_file_loaded(verify):
    bad = valid_lesson()
    del get_ex(bad, "G1", "P01")["translation"]
    result = verify(valid_lesson(), bad)
    line = result.lines_with("MALFORMED_FILE")[0]
    assert "loaded" in line


def test_optional_coda_may_be_absent(verify):
    # Not-triggered: the first beat of the valid lesson has no coda.
    lesson = valid_lesson()
    assert "coda" not in get_ex(lesson, "G2", "B01")["beats"][0]
    result = verify(lesson, clone(lesson))
    assert "MALFORMED_FILE" not in result.codes
    assert result.returncode == 0


def test_fields_of_the_other_type_are_not_required(verify):
    # Not-triggered: pronunciation has no image_file/beats/tiles, build_word has no instruction.
    lesson = valid_lesson()
    assert "beats" not in get_ex(lesson, "G1", "P01")
    assert "instruction" not in get_ex(lesson, "G2", "B01")
    result = verify(lesson, clone(lesson))
    assert result.returncode == 0


# --- Rule 2: DUPLICATE_ID ---------------------------------------------------
def test_duplicate_group_id_in_loaded(verify):
    bad = valid_lesson()
    bad["groups"].append(clone(bad["groups"][0]))
    result = verify(valid_lesson(), bad)
    assert result.returncode == 1
    assert "DUPLICATE_ID" in result.codes


def test_duplicate_group_id_in_source(verify):
    bad = valid_lesson()
    bad["groups"].append(clone(bad["groups"][0]))
    result = verify(bad, valid_lesson())
    assert result.returncode == 1
    assert "DUPLICATE_ID" in result.codes
    assert "source" in result.lines_with("DUPLICATE_ID")[0]


def test_duplicate_exercise_id_in_group(verify):
    bad = valid_lesson()
    get_group(bad, "G1")["exercises"].append(pron_exercise("P01", 2))
    result = verify(valid_lesson(), bad)
    assert result.returncode == 1
    assert "DUPLICATE_ID" in result.codes


def test_duplicate_exercise_id_in_source(verify):
    bad = valid_lesson()
    get_group(bad, "G1")["exercises"].append(pron_exercise("P01", 2))
    result = verify(bad, valid_lesson())
    assert result.returncode == 1
    assert "DUPLICATE_ID" in result.codes


def test_distinct_ids_are_not_duplicates(verify):
    lesson = valid_lesson()
    get_group(lesson, "G1")["exercises"].append(pron_exercise("P02", 2))
    result = verify(lesson, clone(lesson))
    assert "DUPLICATE_ID" not in result.codes
    assert result.returncode == 0


def test_duplicate_id_is_case_sensitive(verify):
    # "p01" and "P01" are different ids, so no duplicate.
    lesson = valid_lesson()
    get_group(lesson, "G1")["exercises"].append(pron_exercise("p01", 2))
    result = verify(lesson, clone(lesson))
    assert "DUPLICATE_ID" not in result.codes


# --- Skip all other checks after MALFORMED_FILE / DUPLICATE_ID --------------
def test_malformed_loaded_skips_source_vs_loaded_checks(verify):
    loaded = valid_lesson()
    del get_ex(loaded, "G1", "P01")["instruction"]
    get_ex(loaded, "G1", "P01")["translation"] = "something else"  # would be FIELD_MISMATCH
    result = verify(valid_lesson(), loaded)
    assert result.returncode == 1
    assert "MALFORMED_FILE" in result.codes
    assert result.codes <= FILE_LEVEL


def test_malformed_source_skips_source_vs_loaded_checks(verify):
    source = valid_lesson()
    del get_ex(source, "G1", "P01")["instruction"]
    loaded = valid_lesson()
    get_ex(loaded, "G1", "P01")["translation"] = "something else"
    result = verify(source, loaded)
    assert "MALFORMED_FILE" in result.codes
    assert result.codes <= FILE_LEVEL


def test_malformed_skips_consistency_checks(verify):
    # Loaded beats do not spell the word (rule 12) but another exercise is malformed.
    loaded = valid_lesson()
    get_ex(loaded, "G2", "B01")["target_word"] = BET + BET
    del get_ex(loaded, "G1", "P01")["audio_file"]
    result = verify(valid_lesson(), loaded)
    assert "MALFORMED_FILE" in result.codes
    assert result.codes <= FILE_LEVEL


def test_malformed_skips_asset_check(verify, tmp_path):
    empty_assets = tmp_path / "empty_assets"
    empty_assets.mkdir()
    bad = valid_lesson()
    del get_ex(bad, "G1", "P01")["audio_file"]
    result = verify(valid_lesson(), bad, "--assets-dir", str(empty_assets))
    assert "MALFORMED_FILE" in result.codes
    assert "ASSET_MISSING" not in result.codes


def test_duplicate_id_skips_source_vs_loaded_checks(verify):
    loaded = valid_lesson()
    loaded["groups"].append(clone(loaded["groups"][0]))      # DUPLICATE_ID
    get_ex(loaded, "G2", "B01")["translation"] = "different"  # would be FIELD_MISMATCH
    del loaded["groups"][1]                                    # would be MISSING_GROUP (G2)
    result = verify(valid_lesson(), loaded)
    assert result.returncode == 1
    assert "DUPLICATE_ID" in result.codes
    assert result.codes <= FILE_LEVEL


def test_duplicate_id_in_source_skips_other_checks(verify):
    source = valid_lesson()
    get_group(source, "G1")["exercises"].append(pron_exercise("P01", 2))
    loaded = valid_lesson()
    get_ex(loaded, "G1", "P01")["translation"] = "different"
    result = verify(source, loaded)
    assert "DUPLICATE_ID" in result.codes
    assert result.codes <= FILE_LEVEL


def test_duplicate_id_skips_consistency_checks(verify):
    loaded = valid_lesson()
    get_ex(loaded, "G2", "B01")["target_word"] = BET + BET   # rule 12 would fire
    loaded["groups"].append(clone(loaded["groups"][0]))
    result = verify(valid_lesson(), loaded)
    assert "DUPLICATE_ID" in result.codes
    assert result.codes <= FILE_LEVEL


def test_malformed_and_duplicate_are_both_reported(verify):
    source = valid_lesson()
    source["groups"].append(clone(source["groups"][0]))        # DUPLICATE_ID in source
    loaded = valid_lesson()
    del get_ex(loaded, "G1", "P01")["target_word"]             # MALFORMED_FILE in loaded
    result = verify(source, loaded)
    assert {"MALFORMED_FILE", "DUPLICATE_ID"} <= result.codes
    assert result.codes <= FILE_LEVEL


def test_without_file_level_problems_other_checks_still_run(verify):
    # Not-triggered counterpart of the skip behavior.
    loaded = valid_lesson()
    get_ex(loaded, "G1", "P01")["translation"] = "something else"
    result = verify(valid_lesson(), loaded)
    assert "FIELD_MISMATCH" in result.codes
