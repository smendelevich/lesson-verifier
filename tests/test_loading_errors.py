"""Loading and the Errors section: exit code 2, message on stderr, no traceback."""
import pytest

from conftest import run_cli, valid_lesson, write_json


def assert_clean_error(result):
    assert result.returncode == 2
    assert result.stderr.strip() != ""
    assert "Traceback" not in result.stderr
    assert result.stdout.strip() == ""


def make_bad_file(tmp_path, kind):
    path = tmp_path / "bad.json"
    if kind == "missing":
        return tmp_path / "does_not_exist.json"
    if kind == "directory":
        path.mkdir()
        return path
    if kind == "invalid_json":
        path.write_text('{"lesson_id": "L01", "groups": [', encoding="utf-8")
    elif kind == "empty_file":
        path.write_bytes(b"")
    elif kind == "not_utf8":
        # 0xFF can never appear in UTF-8
        path.write_bytes(b'{"lesson_id": "L\xff01", "groups": []}')
    elif kind == "cp1255_hebrew":
        # Hebrew saved in a legacy single-byte encoding is not valid UTF-8
        text = '{"lesson_id": "' + "חלב" + '", "groups": []}'
        path.write_bytes(text.encode("cp1255"))
    return path


KINDS = ["missing", "directory", "invalid_json", "empty_file", "not_utf8", "cp1255_hebrew"]


@pytest.mark.parametrize("kind", KINDS)
def test_bad_source_file_exits_2(tmp_path, good_file, kind):
    bad = make_bad_file(tmp_path, kind)
    assert_clean_error(run_cli(bad, good_file, cwd=tmp_path))


@pytest.mark.parametrize("kind", KINDS)
def test_bad_loaded_file_exits_2(tmp_path, good_file, kind):
    bad = make_bad_file(tmp_path, kind)
    assert_clean_error(run_cli(good_file, bad, cwd=tmp_path))


def test_both_files_missing_exits_2(tmp_path):
    result = run_cli(tmp_path / "a.json", tmp_path / "b.json", cwd=tmp_path)
    assert_clean_error(result)


def test_error_message_mentions_the_bad_file(tmp_path, good_file):
    bad = make_bad_file(tmp_path, "missing")
    result = run_cli(good_file, bad, cwd=tmp_path)
    assert bad.name in result.stderr


def test_valid_utf8_hebrew_file_loads_without_error(verify):
    # Not-triggered counterpart: Hebrew written as real UTF-8 is fine.
    result = verify(valid_lesson(), valid_lesson())
    assert result.returncode == 0
    assert result.stderr.strip() == ""


# --- usage errors (exit code 2) --------------------------------------------
def test_no_arguments_exits_2(tmp_path):
    result = run_cli(cwd=tmp_path)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_one_argument_exits_2(tmp_path, good_file):
    result = run_cli(good_file, cwd=tmp_path)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_unknown_format_value_exits_2(tmp_path, good_file):
    result = run_cli(good_file, good_file, "--format", "xml", cwd=tmp_path)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr


def test_valid_json_but_missing_field_is_not_an_exit_2(tmp_path, good_file):
    # Boundary: "valid JSON with a missing required field" is exit 1, not 2.
    lesson = valid_lesson()
    del lesson["lesson_id"]
    bad = write_json(tmp_path / "nolid.json", lesson)
    result = run_cli(bad, good_file, cwd=tmp_path)
    assert result.returncode == 1
    assert "MALFORMED_FILE" in result.stdout
