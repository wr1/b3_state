"""Tests for CLI."""

import pytest
from b3_state.cli.main import run


def test_cli(tmp_path):
    """Test the CLI run function."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("workdir: work_dir\ntest:\n  subkey: value")

    # Call the CLI run function with force=True to trigger execution
    with pytest.raises(NotImplementedError):
        run(str(config_path), force=True)

    # Check that workdir was created
    workdir = tmp_path / "work_dir"
    assert workdir.exists()
