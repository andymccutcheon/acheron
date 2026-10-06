from types import SimpleNamespace

from acheron.bm import _is_error, _text_of, normalize_results


def test_normalize_results_maps_fields_and_collapses_whitespace():
    payload = {
        "results": [
            {
                "title": "Memory",
                "entity": "demo/concepts/memory",
                "permalink": "demo/concepts/memory",
                "file_path": "concepts/Memory.md",
                "project": "demo",
                "matched_chunk": "# Memory\n\nline   one\nline two",
                "score": 1.23,
            }
        ]
    }
    out = normalize_results(payload)
    assert len(out) == 1
    item = out[0]
    assert item["title"] == "Memory"
    assert item["path"] == "demo/concepts/memory"
    assert item["file_path"] == "concepts/Memory.md"
    assert item["project"] == "demo"
    assert item["snippet"] == "# Memory line one line two"
    assert item["native_score"] == 1.23


def test_normalize_results_tolerates_missing_fields():
    out = normalize_results({"results": [{"title": "T"}]})
    assert out[0]["path"] == ""
    assert out[0]["snippet"] == ""


def test_text_and_error_helpers_both_sdk_shapes():
    snake = SimpleNamespace(content=[SimpleNamespace(text="hello")], is_error=False)
    camel = SimpleNamespace(content=[SimpleNamespace(text="bye")], isError=True)
    assert _text_of(snake) == "hello"
    assert _text_of(camel) == "bye"
    assert _is_error(snake) is False
    assert _is_error(camel) is True
