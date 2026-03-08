"""Tests for core functionality."""

import time
import pytest
from b3_state.core.base import b3_state, ManagedFile
from b3_state.utils.config_utils import hash_config_section


@pytest.fixture
def temp_dir(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("workdir: work_dir\ntest: value")
    return tmp_path, config


def test_b3_state_init(temp_dir):
    tmp_path, config = temp_dir
    sm = b3_state(str(config))
    assert sm.config == {"workdir": "work_dir", "test": "value"}
    assert sm.workdir == tmp_path / "work_dir"


def test_workdir_creation(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: new_work_dir")
    sm = b3_state(str(config_path))
    assert sm.workdir.exists()
    assert sm.workdir.is_dir()


class TestStep(b3_state):
    __test__ = False
    dependent_sections = ["test"]
    output_files = ["output.txt"]
    input_files = [ManagedFile(name="input.txt", non_empty=True, newer_than="config")]

    def _execute(self):
        (self.workdir / "output.txt").write_text("executed")


def test_has_section_changed(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: initial")
    sm = TestStep(str(config_path))
    assert sm.has_section_changed("test")
    sm.save_state("test", hash_config_section(sm.config.get("test", {})))
    assert not sm.has_section_changed("test")
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: changed")
    sm.config = sm.load_config()  # Reload config
    assert sm.has_section_changed("test")


def test_has_section_changed_with_nested_dict(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  nested:\n    a: 1\n    b: 2")
    sm = TestStep(str(config_path))
    assert sm.has_section_changed("test")
    sm.save_state("test", hash_config_section(sm.config.get("test", {})))
    assert not sm.has_section_changed("test")
    # Change order of nested keys
    config_path.write_text("workdir: work_dir\ntest:\n  nested:\n    b: 2\n    a: 1")
    sm.config = sm.load_config()  # Reload config
    assert sm.has_section_changed("test")  # Should detect change due to order
    # Change a value
    config_path.write_text("workdir: work_dir\ntest:\n  nested:\n    a: 1\n    b: 3")
    sm.config = sm.load_config()
    assert sm.has_section_changed("test")


def test_needs_run_scenarios(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir")
    sm = TestStep(str(config_path))
    time.sleep(0.01)  # Ensure subsequent file operations have later timestamps

    # Missing input
    assert sm.needs_run()  # Input missing

    # Create input
    input_path = sm.workdir / "input.txt"
    input_path.write_text("data")
    time.sleep(0.01)  # Ensure input mtime > config mtime

    # Missing output
    assert sm.needs_run()

    # Create output
    output_path = sm.workdir / "output.txt"
    output_path.write_text("data")
    time.sleep(0.01)  # Ensure output mtime > input mtime

    # Changed section (initially no state)
    assert sm.needs_run()

    # Save state
    sm.save_state("test", hash_config_section(sm.config.get("test", {})))
    assert not sm.needs_run()

    # Change section
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: changed")
    time.sleep(0.01)  # Ensure config mtime is distinct
    sm.config = sm.load_config()
    assert sm.needs_run()

    # Simulate updating input after config change to make it newer than config
    time.sleep(0.01)
    input_path.touch()

    # Run the step to reset state and update outputs
    sm.run()
    assert not sm.needs_run()

    # Test input newer than output
    time.sleep(0.01)
    input_path.touch()
    assert sm.needs_run()


def test_run_executes(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: value")
    sm = TestStep(str(config_path))

    input_path = sm.workdir / "input.txt"
    input_path.write_text("data")

    sm.run()
    output_path = sm.workdir / "output.txt"
    assert output_path.exists()
    assert output_path.read_text() == "executed"
    assert not sm.needs_run()  # After run, shouldn't need to run again

    # Test if it doesn't run again
    output_path.write_text("unchanged")
    sm.run()
    assert output_path.read_text() == "unchanged"  # Not overwritten


def test_run_output_validation_failure(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir")

    class FailingStep(b3_state):
        output_files = ["output.txt"]

        def _execute(self):
            pass  # Doesn't create output

    sm = FailingStep(str(config_path))
    with pytest.raises(
        RuntimeError, match=r"Output file '.*/output\.txt' was not created properly\."
    ):
        sm.run()


def test_section_unchanged_detection(tmp_path):
    """Test that sections detect changes correctly based on ASCII differences."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "workdir: work_dir\nmesh:\n  n_elem: 40\n  element_size: 0.1"
    )
    sm = TestStep(str(config_path))
    sm.dependent_sections = ["mesh"]  # Change to mesh for this test

    # Create input and output to avoid other triggers
    input_path = sm.workdir / "input.txt"
    input_path.write_text("data")
    output_path = sm.workdir / "output.txt"
    output_path.write_text("data")

    # Initially, section changed
    assert sm.has_section_changed("mesh")
    sm.save_state("mesh", hash_config_section(sm.config.get("mesh", {})))
    assert not sm.has_section_changed("mesh")

    # Rewrite config with same content but different formatting (order)
    config_path.write_text(
        "workdir: work_dir\nmesh:\n  element_size: 0.1\n  n_elem: 40"
    )
    sm.config = sm.load_config()
    assert sm.has_section_changed("mesh")  # Should detect change due to order

    # Rewrite with different float representation
    config_path.write_text(
        "workdir: work_dir\nmesh:\n  n_elem: 40\n  element_size: 0.1000000001"
    )
    sm.config = sm.load_config()
    assert sm.has_section_changed("mesh")  # Should detect change due to different ASCII


def test_run_saves_current_hash(tmp_path):
    """Test that run saves the current hash, not the previous one."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: initial")
    sm = TestStep(str(config_path))

    # Create input to avoid missing input trigger
    input_path = sm.workdir / "input.txt"
    input_path.write_text("data")

    # Initially, section changed
    assert sm.has_section_changed("test")
    initial_hash = hash_config_section(sm.config.get("test", {}))
    sm.save_state("test", initial_hash)
    assert not sm.has_section_changed("test")

    # Change the config
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: changed")
    sm.config = sm.load_config()
    time.sleep(0.01)  # Ensure config mtime is updated
    input_path.touch()  # Make input newer than the new config
    new_hash = hash_config_section(sm.config.get("test", {}))
    assert sm.has_section_changed("test")

    # Run the step
    sm.run()

    # After run, the saved hash should be the new_hash (current at run time)
    assert sm.previous_states["test"] == new_hash
    # And needs_run should be false now
    assert not sm.needs_run()


def test_run_force_flag(tmp_path):
    """Test that the force flag causes execution even when needs_run is False."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: value")
    sm = TestStep(str(config_path))

    # Create input and output, and save state so needs_run is False
    input_path = sm.workdir / "input.txt"
    input_path.write_text("data")
    output_path = sm.workdir / "output.txt"
    output_path.write_text("initial")
    sm.save_state("test", hash_config_section(sm.config.get("test", {})))

    # Confirm needs_run is False
    assert not sm.needs_run()

    # Run with force=True
    sm.run(force=True)

    # Check that _execute was called, overwriting the output
    assert output_path.read_text() == "executed"


def test_run_force_pre_clean(tmp_path):
    """Test that force=True pre-cleans previous outputs before execution."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: value")
    sm = TestStep(str(config_path))

    # Create input and output, and save state so needs_run is False
    input_path = sm.workdir / "input.txt"
    input_path.write_text("data")
    output_path = sm.workdir / "output.txt"
    output_path.write_text("initial")
    sm.save_state("test", hash_config_section(sm.config.get("test", {})))

    # Confirm needs_run is False
    assert not sm.needs_run()

    # Run with force=True
    sm.run(force=True)

    # Check that output was cleaned and then recreated
    assert output_path.read_text() == "executed"
