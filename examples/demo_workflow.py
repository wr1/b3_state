"""Demo workflow using b3_state."""

import json
import time
from pathlib import Path

from b3_state.core.base import b3_state, ManagedFile


class P1Step(b3_state):
    """Step 1: Interpolate parameters."""

    workdir_key = "paths.workdir"
    dependent_sections = ["geometry"]
    output_files = ["output.json", "output.vtu"]

    def _execute(self):
        self.logger.info("Executing P1Step: Interpolating parameters.")
        output_json = self.workdir / "output.json"
        output_vtu = self.workdir / "output.vtu"
        with open(output_json, "w") as f:
            json.dump(self.config["geometry"], f)
        with open(output_vtu, "w") as f:
            f.write("Dummy VTU data")


class P2Step(b3_state):
    """Step 2: Mesh according to parameters."""

    workdir_key = "paths.workdir"
    input_files = [
        ManagedFile(name="output.json", non_empty=True, newer_than="config"),
        ManagedFile(name="output.vtu", non_empty=True, newer_than="config"),
    ]

    of1 = "output2.json"
    output_files = [of1]
    dependent_sections = ["geometry"]

    def _execute(self):
        self.logger.info("Executing P2Step: Meshing according to parameters.")
        output_json2 = self.workdir / "output2.json"
        with open(output_json2, "w") as f:
            json.dump({"meshed": True}, f)


# Medium complex demo
if __name__ == "__main__":
    config_path = Path(__file__).parent / "sample_config.yaml"
    p1 = P1Step(str(config_path))
    p1.run()
    p2 = P2Step(str(config_path))
    p2.run()

    print("After initial run, p2.needs_run():", p2.needs_run())  # Should be False

    # Demonstrate that nested dict order doesn't affect change detection
    print("Modifying config with same nested dict but different key order...")
    config_path.write_text(
        "paths:\n  workdir: demo_dir\ngeometry:\n  params:\n    param2: value2\n    param1: value1\n"
    )
    p2.config = p2.load_config()  # Reload config
    print(
        "After reloading config with reordered keys, p2.needs_run():", p2.needs_run()
    )  # Should still be False

    # Demonstrate input file management: if input is newer than output, needs rerun
    print("Before modification, needs_run:", p2.needs_run())  # Should be False
    time.sleep(1)  # Ensure timestamp difference
    input_path = p2.workdir / "output.json"
    with open(input_path, "w") as f:
        json.dump({"geometry": "modified"}, f)
    print("Modified input file to make it newer.")
    print("After modification, needs_run:", p2.needs_run())  # Should be True
    p2.run()  # Should re-execute

    # Demonstrate force run
    print("After re-run, needs_run:", p2.needs_run())  # Should be False
    print("Running with force=True to demonstrate forced execution.")
    p2.run(force=True)  # Should execute even though needs_run is False
    print("Force run completed.")
