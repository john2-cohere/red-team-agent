from pathlib import Path
import json
import os

def remove_empty_json_files(reports_dir: Path):
    """Remove JSON files that are empty or contain empty JSON objects"""
    removed_count = 0
    
    for report_file in reports_dir.glob("*.json"):
        try:
            with open(report_file, "r") as f:
                report = json.load(f)
                
            # Check if report is empty (None, empty dict, or empty content)
            if (not report or 
                report == {} or
                (isinstance(report, dict) and not any(report.values()))):
                    
                os.remove(report_file)
                print(f"Removed empty file: {report_file}")
                removed_count += 1
                
        except json.JSONDecodeError:
            # File contains invalid JSON, remove it
            os.remove(report_file)
            print(f"Removed invalid JSON file: {report_file}")
            removed_count += 1
            
    print(f"\nTotal files removed: {removed_count}")

if __name__ == "__main__":
    reports_dir = Path("scrapers/reports")
    remove_empty_json_files(reports_dir)
