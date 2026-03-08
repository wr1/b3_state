"""Demo workflow showing mesh section change management."""

import json
import logging
from pathlib import Path

from rich.logging import RichHandler
from b3_state.core.base import b3_state

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler()],
)


class MeshStep(b3_state):
    """Step that depends on mesh section."""

    workdir_key = "general.workdir"
    dependent_sections = ["mesh"]
    output_files = ["mesh_output.json"]

    def _execute(self):
        self.logger.info("Executing MeshStep: Processing mesh parameters.")
        output_json = self.workdir / "mesh_output.json"
        with open(output_json, "w") as f:
            json.dump(self.config["mesh"], f)


if __name__ == "__main__":
    config_path = Path(__file__).parent / "sample_config.yaml"
    mesh_step = MeshStep(str(config_path))

    # Clean up previous outputs and state for demo
    output_file = mesh_step.workdir / "mesh_output.json"
    state_file = mesh_step.state_file
    if output_file.exists():
        output_file.unlink()
        mesh_step.logger.info(f"Removed existing output file: {output_file}")
    if state_file.exists():
        state_file.unlink()
        mesh_step.logger.info(f"Removed existing state file: {state_file}")

    mesh_step.logger.info("Initial check")
    print("Initial needs_run:", mesh_step.needs_run())
    mesh_step.run()
    print("After run, needs_run:", mesh_step.needs_run())

    # Modify the mesh section
    mesh_step.logger.info("Modifying mesh section...")
    config_content = config_path.read_text()
    # Change n_elem from 40 to 50
    modified_content = config_content.replace("n_elem: 40", "n_elem: 50")
    config_path.write_text(modified_content)
    mesh_step.config = mesh_step.load_config()  # Reload config
    mesh_step.logger.info("After modifying mesh, checking needs_run")
    print("After modifying mesh, needs_run:", mesh_step.needs_run())
    mesh_step.run()
    print("After re-run, needs_run:", mesh_step.needs_run())

    # Test with float change
    mesh_step.logger.info("Modifying float in mesh...")
    modified_content = modified_content.replace(
        "element_size: 0.10", "element_size: 0.11"
    )
    config_path.write_text(modified_content)
    mesh_step.config = mesh_step.load_config()
    mesh_step.logger.info("After modifying float, checking needs_run")
    print("After modifying float, needs_run:", mesh_step.needs_run())
