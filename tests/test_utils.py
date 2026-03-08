"""Tests for utils."""

from b3_state.utils.config_utils import hash_config_section
from b3_state.utils.file_utils import get_file_mtime, is_file_non_empty


def test_hash_config_section():
    section = {"key": "value"}
    hash1 = hash_config_section(section)
    assert isinstance(hash1, str)
    assert len(hash1) == 64  # SHA-256 hex
    hash2 = hash_config_section(section)
    assert hash1 == hash2
    different = {"key": "different"}
    assert hash_config_section(different) != hash1
    # Test with nested dict
    nested = {"a": {"b": 1, "c": 2}}
    hash_nested = hash_config_section(nested)
    # Same nested but different order
    nested_reordered = {"a": {"c": 2, "b": 1}}
    assert hash_config_section(nested_reordered) != hash_nested


def test_file_utils(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.touch()
    assert not is_file_non_empty(empty)

    non_empty = tmp_path / "non_empty.txt"
    non_empty.write_text("data")
    assert is_file_non_empty(non_empty)

    missing = tmp_path / "missing.txt"
    assert get_file_mtime(missing) == 0.0

    assert get_file_mtime(non_empty) > 0
