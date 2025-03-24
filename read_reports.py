from pathlib import Path
import json
from nietzkit.johnllm import LMP, LLMModel
from pydantic import BaseModel
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

class EngagementType(str, Enum):
    WEB = "web"
    OTHER = "other"
    
class ReportData(BaseModel):
    report_type: EngagementType

class ClassifyReport(LMP):
    prompt = """
{{content}}

Classify the report type:
web -> web applications and APIs, does not include web-related software
other -> all other types of reports
"""
    response_format = ReportData
    
REPORTS_DIR = Path("scrapers/reports")
model = LLMModel()

# for r in list(REPORTS_DIR.glob("*.json")):
#     print("Classifying report", r)
#     contents = json.loads(r.read_text())
#     if contents and contents.get("content", None):
#         prompt_args = {"content": contents["content"]}
#         res = ClassifyReport().invoke(model,
#                                  model_name="deepseek", 
#                                  prompt_args=prompt_args)
#         with open(r, "w") as f:
#             contents["report_type"] = res.report_type
#             f.write(json.dumps(contents))        

for r in list(REPORTS_DIR.glob("*.json")):
    contents = json.loads(r.read_text(encoding="utf-8"))
    if contents and contents.get("content", None) and contents.get("report_type", None) == EngagementType.OTHER:
        try:
            print("Report: ", r)
            print(contents["content"])
        except:
            continue

        # res = ClassifyReport().invoke(model,
        #                          model_name="deepseek", 
        #                          prompt_args=prompt_args)
        # with open(r, "w") as f:
        #     contents["report_type"] = res.report_type
        #     f.write(json.dumps(contents))        

# def process_report(report_path):
#     # print("Classifying report", report_path)
#     contents = json.loads(report_path.read_text())
#     if contents and contents.get("content", None):
#         prompt_args = {"content": contents["content"]}
#         res = ClassifyReport().invoke_mt(model,
#                                     model_name="deepseek", 
#                                     prompt_args=prompt_args)
#         with open(report_path, "w") as f:
#             contents["report_type"] = res.report_type
#             f.write(json.dumps(contents))

# with ThreadPoolExecutor(max_workers=5) as executor:
#     report_files = list(REPORTS_DIR.glob("*.json"))
#     executor.map(process_report, report_files)