"""
Probe 1 v5 Test File - Main Module
Purpose: Validate GitHub Annotations extraction for GeneralCoder (D-1b)

This file imports from probe1_v5_utils.py and contains additional lint errors.
Together, these two files test multi-file extraction via Annotations API.

Test validation checklist:
- [ ] Annotations extracted from lint check_run
- [ ] ci_error_file_paths contains both files
- [ ] review_files set in orchestrator initial_state
- [ ] GeneralCoder triggered (not SimpleCoder)
- [ ] Both files included in fix attempt
"""

from probe1_v5_utils import calculate_total, format_output, validate_input


def process_data(raw_data: list) -> dict:
    """Process raw data and return formatted result."""
    # Intentional F821 error: 'validator' is not defined
    if not validator.check(raw_data):
        return {"error": "Invalid data"}

    total = calculate_total(raw_data)
    return {"total": total, "count": len(raw_data)}


def run_pipeline(config: dict) -> str:
    """Run the data processing pipeline."""
    # Intentional F821 error: 'config_loader' is not defined
    settings = config_loader.load(config)

    data = settings.get("data", [])
    if validate_input(str(data)):
        result = process_data(data)
        return format_output(result)
    return "No data"


if __name__ == "__main__":
    sample_config = {"data": [1, 2, 3, 4, 5]}
    output = run_pipeline(sample_config)
    print(output)
