"""Utilities for config operations."""

import hashlib
from io import StringIO
from typing import Any, Dict

import ruamel.yaml as yaml


def hash_config_section(section: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of a config section using ruamel.yaml for string representation preserving order."""
    # Dump the section to YAML string preserving order and formatting
    stream = StringIO()
    y = yaml.YAML()
    y.dump(section, stream)
    yaml_str = stream.getvalue()
    return hashlib.sha256(yaml_str.encode()).hexdigest()
