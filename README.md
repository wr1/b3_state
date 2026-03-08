# b3_state

b3_state is a Python library for managing states in file-system-based workflows, enabling dependency checks, restarts, and partial iterations for expensive computational steps.

## Installation

```bash
pip install b3_state
```

Alternatively, using uv:
```bash
uv pip install b3_state
```

## Usage

Define workflow steps by subclassing `b3_state` and using Pydantic models for state validation.

The working directory can be specified in the config YAML under the key `workdir` (default) or an alternative key by setting the `workdir_key` class attribute to a dotted path, e.g., `'paths.workdir'` for nested configurations.

See `examples/demo_workflow.py` for a demonstration. To run the demo:
```bash
python examples/demo_workflow.py
```

## Development

- Install dependencies with uv: `uv sync --all-extras`
- Run tests: `uv run pytest`
- Format and check code: `uv run ruff format` and `uv run ruff check --fix`
