from io import StringIO

import pytest

from src.json_repair.json_repair import load, repair_json


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ('"a": 1}', {"a": 1}),
        ('\n    "a" : 1\n}', {"a": 1}),
        ('"a": 1, "b": [true, {"c": 2}]}', {"a": 1, "b": [True, {"c": 2}]}),
        (r'"a\"b": 1}', {'a"b': 1}),
        ('"http:resource": "value"}', {"http:resource": "value"}),
        ('"": false}', {"": False}),
        ('"a": 1', {"a": 1}),
    ],
)
def test_repair_missing_opening_object_brace(source, expected):
    assert repair_json(source, return_objects=True) == expected


def test_missing_opening_object_brace_is_logged():
    result, logs = repair_json('"a": 1}', logging=True)
    assert result == {"a": 1}
    assert any("missing opening" in entry["text"].lower() for entry in logs)


def test_strict_rejects_missing_opening_object_brace():
    with pytest.raises(ValueError, match="Missing opening"):
        repair_json('"a": 1}', strict=True)


@pytest.mark.parametrize("skip_json_loads", [False, True])
def test_load_missing_opening_object_brace(skip_json_loads):
    fd = StringIO('ignored prefix\n  "a\\\"b": 1}')
    fd.seek(len("ignored prefix\n"))
    assert load(fd, skip_json_loads=skip_json_loads, chunk_length=2) == {'a"b': 1}


def test_missing_opening_object_brace_with_schema():
    schema = {"type": "object", "properties": {"a": {"type": "integer"}}, "required": ["a"]}
    assert repair_json('"a": 1}', schema=schema, return_objects=True) == {"a": 1}


@pytest.mark.parametrize("source", ['"a: b"', '"a\\\"b"', '"a\\\\b"'])
def test_valid_quoted_root_strings_are_preserved(source):
    assert repair_json(source) == source


@pytest.mark.parametrize("source", ['"unterminated', '"unterminated\\', '"key"', 'before "key": 1}'])
def test_missing_opening_brace_requires_an_initial_quoted_key_and_colon(source):
    assert repair_json(source, skip_json_loads=True) == ""
