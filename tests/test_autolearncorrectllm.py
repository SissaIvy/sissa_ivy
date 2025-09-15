import subprocess
import sys
from pathlib import Path


def test_spec_file_exists():
    spec_path = Path(__file__).parent.parent / "archetypes" / "auto_learn_correct.llm.v0.1.0.json"
    assert spec_path.exists(), f"Spec file not found: {spec_path}"


def test_cli_prints_json():
    # Run the CLI and check for valid JSON output
    cli_path = Path(__file__).parent.parent / "archetypes" / "auto_learn_correct_llm.py"
    result = subprocess.run([sys.executable, str(cli_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"CLI exited with {result.returncode}: {result.stderr}"
    # Should be valid JSON
    import json
    try:
        data = json.loads(result.stdout)
    except Exception as e:
        raise AssertionError(f"CLI did not output valid JSON: {e}\nOutput: {result.stdout}")
    assert isinstance(data, dict), "Spec output is not a JSON object"
