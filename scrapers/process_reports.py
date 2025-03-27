from johnllm import LLMModel, LMP
from pydantic import BaseModel
from enum import Enum
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class VulnCategory(str, Enum):
    WEB_APP = "WEB_APP"
    API = "API" 
    MOBILE = "MOBILE"
    IOT = "IOT"
    CODE = "CODE"

class Report(BaseModel):
    category: VulnCategory

class CategorizeReports(LMP):
    prompt = """
{{report}}

The above is a report for a vulnerability. Please categorize it into one of the following categories:

WEB_APP:  a vuln in *deployed* software. a network vulnerability that requires some interaction with a user interface (that is, this is not *strictly* required since the interface action may be triggered by an API call but the in the report the finding originates from the interface)
API: a vuln in *deployed* software. a network vulnerability that does not require some interaction with a user interface
MOBILE: all mobile originating vulnerabilities
IOT: all IOT vulns should be here, including random hardware things
CODE: the vulnerability exists *intrinsically* in some software package, rather than a deployed application. all new vulnerabilities should be categorized here. the exploitation of existing vulns in * deployed* software should either go under API or WEB_APP
"""
    response_format = Report

def classify_report(llm_model: LLMModel, report) -> Report:
    report_str = f"Title: {report['title']}"
    report_str += f"Description: \n{report['content']}"
    
    return CategorizeReports().invoke(
        model=llm_model,
        model_name="deepseek",
        prompt_args={
            "report": report_str
        }
    )

def read_reports_in_batches(reports_dir: Path, batch_size: int = 50):
    """Generator that yields batches of reports from JSON files"""
    batch = []
    for report_file in reports_dir.glob("*.json"):
        with open(report_file, "r") as f:
            report = json.load(f)
            if not report:
                continue

            report["_file"] = report_file  # Store filename for later
            batch.append(report)
            
        if len(batch) >= batch_size:
            yield batch
            batch = []
            
    if batch:  # Yield any remaining reports
        yield batch

if __name__ == "__main__":
    BATCH_NUM = 8
    
    batch_index = 0
    llm = LLMModel()
    reports_dir = Path("scrapers/reports")

    def process_report(report, pbar):
        result = classify_report(llm, report)
        report["vuln_category"] = result.category
        
        with open(report["_file"], "w") as f:
            print(f"Report {report['_file']} categorized as {result.category}")
            # Remove temp filename before saving
            report_to_save = report.copy()
            del report_to_save["_file"]
            json.dump(report_to_save, f, indent=2)
        
        pbar.update(1)
        return result.category

    with ThreadPoolExecutor(max_workers=3) as executor:
        while batch_index < BATCH_NUM:
            # Get first batch and process it
            batch = next(read_reports_in_batches(reports_dir))
            
            with tqdm(total=len(batch), desc=f"Processing batch {batch_index + 1}/{BATCH_NUM}") as pbar:
                results = list(executor.map(lambda x: process_report(x, pbar), batch))
            
            batch_index += 1
            print(f"Processed {batch_index} batches")
