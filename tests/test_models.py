"""Tests for models."""

import time
import pytest
from b3_state.models.state import FileState


@pytest.fixture
def temp_dir(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("workdir: work_dir\ntest: value")
    return tmp_path, config


def test_file_state_validation(temp_dir):
    tmp_path, config = temp_dir
    time.sleep(0.01)  # Ensure file is created after config for mtime difference
    file = tmp_path / "test.txt"
    file.write_text("data")
    state = FileState(path=file, newer_than=config)
    assert state.path == file


def test_file_state_validation_errors(tmp_path):
    non_existent = tmp_path / "missing.txt"
    with pytest.raises(ValueError, match="File does not exist"):
        FileState(path=non_existent)

    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    with pytest.raises(ValueError, match="File is empty"):
        FileState(path=empty_file, non_empty=True)

    old_file = tmp_path / "old.txt"
    old_file.write_text("data")
    time.sleep(1)
    new_file = tmp_path / "new.txt"
    new_file.write_text("data")
    with pytest.raises(ValueError, match="File .* is not newer than"):
        FileState(path=old_file, newer_than=new_file)
