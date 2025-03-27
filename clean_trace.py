import json

def remove_screenshots(obj):
    """Recursively remove all 'screenshot' keys from a JSON object"""
    if isinstance(obj, dict):
        return {k: remove_screenshots(v) for k, v in obj.items() if k != "screenshot"}
    elif isinstance(obj, list):
        return [remove_screenshots(item) for item in obj]
    else:
        return obj

def clean_trace_file(filepath):
    """Read JSON file, remove screenshots, and write back to same file"""
    # Read the JSON file
    with open(filepath, "r") as f:
        data = json.load(f)

    # Remove screenshots
    cleaned_data = remove_screenshots(data)

    # Write back to same file
    with open(filepath, "w") as f:
        json.dump(cleaned_data, f, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python clean_trace.py <trace_file.json>")
        sys.exit(1)

    trace_file = sys.argv[1]
    clean_trace_file(trace_file)
