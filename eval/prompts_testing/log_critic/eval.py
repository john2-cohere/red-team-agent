from pathlib import Path
from langchain_cohere import ChatCohere
from langchain_deepseek import ChatDeepSeek

DATA_DIR = Path("eval/prompts_testing/log_critic/data")
TEST_AGGREGATOR = """
Results for failed_went_to_github.log:
| Dimension | What went wrong | Evidence | Suggested fix |
|---|---|---|---|
| **A** | The agent pursued unrelated tasks, such as exploring GitHub pages, instead of completing the original task of navigating to http://localhost:3000 and performing specific actions. | Step 10: Navigated to GitHub Copilot page instead of focusing on the original task. | Implement a task adherence check to ensure actions align with the original goal. |
| **B** | The plan expanded excessively, including irrelevant steps like exploring GitHub features, which are unrelated to the original task. | Step 10: Plan included steps to explore GitHub pages, deviating from the main task. | Add a plan validation step to prune irrelevant actions and maintain focus on the original task. |
| **C** | The agent navigated to external domains (e.g., GitHub) despite the "stay on site" rule. | Step 10: Navigated to https://github.com/features/copilot, violating the domain restriction. | Enforce a domain check to block actions leading to external sites. |
| **F** | Self-evaluations were unclear or missing, making it difficult to assess progress. | Multiple steps had "Unknown" evaluations, lacking clarity on success. | Enhance evaluation logic to provide explicit success/failure feedback for each action. |
| **H** | The agent exceeded the step limit without detecting futility, leading to unnecessary runtime. | Step 13: Shutdown initiated after 13/20 steps without completing the original task. | Implement a step counter with a threshold to trigger early termination if the task remains incomplete. |

**Note:** Dimensions D, E, and G were not flagged as they didn't show clear violations in the provided log.

Processing failed_went_to_github.log...

Results for failed_went_to_github.log:
| Dimension | What went wrong | Evidence | Suggested fix |
|---|---|---|---|
| **A** | The agent deviated from the original task of completing part1 and part2, instead focusing on exploring external sites like GitHub. | Step 10: Navigated to GitHub Copilot page instead of returning to the original task. | Implement a task adherence check to ensure actions align with the original task description. |
| **D** | The agent's memory grew monotonically without summarization, storing raw transcripts instead of summaries. | MESSAGE_LEN increased from 3 to 14 without summarization. | Enforce memory summarization after each step to prevent excessive growth. |
| **F** | Self-evaluations were unclear, often stating "Unknown" or merely restating actions without judging success. | Step 1: "Unknown - No previous actions to evaluate." | Enhance evaluation logic to provide clear success/failure judgments based on action outcomes. |
| **H** | The agent exceeded the step counter (20 steps) without detecting futility, leading to premature shutdown. | Step 13: Initiated shutdown after 13 steps without completing the task. | Add a futility detection mechanism to monitor task progress and trigger early termination if stuck. |
| **G** | The agent triggered unnecessary HTTP requests to external sites (e.g., GitHub), increasing I/O load. | Step 10: Requests to GitHub assets and APIs. | Restrict external requests to the target domain (localhost:3000) to reduce I/O overhead. |
| **E** | The agent used stale numeric indices after DOM changes, leading to incorrect element selection. | Step 10: Clicked index 3 (GitHub Copilot) instead of returning to the original task. | Validate element indices after each DOM change to ensure accuracy. |
| **B** | The plan exploded in length, repeating identical steps and including obvious no-ops. | Plan included redundant steps like reopening the sidenav multiple times. | Optimize plan generation to avoid redundancy and prioritize task-critical actions. |
| **C** | The agent navigated off the target domain (localhost:3000) to external sites (GitHub). | Step 10: Navigated to https://github.com/features/copilot. | Enforce a "stay on site" rule to prevent navigation away from the target domain. |

Processing failed_went_to_github.log...

Results for failed_went_to_github.log:
| Dimension | What went wrong | Evidence | Suggested fix |
|---|---|---|---|
| **A** | Agent deviated from the original task of completing part1 and part2, instead focusing on exploring external sites like GitHub. | Step 10: Navigated to GitHub Copilot page instead of returning to the original task. | Implement a task adherence check to ensure actions align with the original task description. |
| **B** | Plan expanded excessively with repeated steps (e.g., reopening sidenav) and irrelevant actions (e.g., exploring GitHub). | Step 2: Generated a lengthy plan with repeated steps like reopening the sidenav. | Add a plan pruning mechanism to remove redundant steps and enforce relevance to the task. |
| **C** | Agent navigated off-domain to GitHub despite the "stay on site" rule. | Step 10: Navigated to https://github.com/features/copilot. | Enforce domain checks to block actions leading to external sites. |
| **D** | MESSAGE_LEN grew monotonically, indicating raw transcript storage instead of summarization. | MESSAGE_LEN increased from 3 to 14 without summarization. | Implement memory summarization to keep context concise. |
| **F** | Self-evaluations were unclear or missing, making progress assessment difficult. | Step 2: Evaluation was "Unknown" despite clear actions. | Enhance evaluation logic to provide clear success/failure judgments. |
| **H** | Exceeded step limit (20 steps) without detecting futility, leading to premature shutdown. | Step 13: Shutdown initiated after 13 steps without completing the task. | Add a futility detection mechanism to recognize when the task cannot be completed. |

**Note:** Dimensions E and G were not flagged as they didn't show clear violations in the provided log.

Processing failed_went_to_github.log...

Results for failed_went_to_github.log:
| Dimension | What went wrong | Evidence | Suggested fix |
|---|---|---|---|
| **A** | The agent deviated from the original task of navigating to http://localhost:3000, logging in, and completing part1 and part2. Instead, it focused on exploring external sites like GitHub, ignoring the primary objectives. | Step 10: Navigated to GitHub Copilot page instead of returning to the task. | Prioritize task adherence by checking if actions align with the original goals before execution. |
| **H** | The agent exceeded the step counter (20 steps) without detecting futility, leading to unnecessary actions and runtime inefficiency. | Step 13: Continued exploring GitHub despite reaching step 13/20 without task progress. | Implement a step counter limit and a futility detection mechanism to halt execution when goals aren't met within the budget. |
| **C** | The agent navigated off the target domain (http://localhost:3000) to external sites like GitHub, violating the "stay on site" rule. | Step 10: Navigated to https://github.com/features/copilot. | Enforce domain checks; reject actions leading to external hosts unless explicitly allowed. |
| **F** | Self-evaluations were unclear or missing, with "Unknown" or generic success messages not reflecting actual progress. | Step 1: "Unknown - No previous actions to evaluate." | Enhance evaluation logic to provide specific success/failure criteria based on observable changes. |
| **G** | The agent triggered excessive HTTP requests to external sites (e.g., GitHub assets, images), causing inefficiency. | Step 10: 16 HTTP requests to GitHub resources. | Restrict external requests by filtering URLs to the target domain only. |
| **B** | The plan expanded unnecessarily, repeating steps (e.g., reopening sidenav) and adding irrelevant actions (e.g., exploring GitHub). | Step 29: Repeated "Open Sidenav" action. | Prune redundant steps and validate plan relevance to the task before execution. |
| **D** | The message length (MESSAGE_LEN) grew monotonically, indicating potential memory bloat from storing raw transcripts. | Step 13: MESSAGE_LEN AFTER: 14. | Summarize transcripts and manage memory efficiently to prevent token count growth. |
| **E** | The agent used stale numeric indices for element selection, leading to incorrect clicks after DOM changes. | Step 3: Clicked index 0 (menu) multiple times without verifying element relevance. | Validate element indices dynamically after each action to ensure accuracy. |

Processing failed_went_to_github.log...

Results for failed_went_to_github.log:
| Dimension | What went wrong | Evidence | Suggested fix |
|---|---|---|---|
| **A** | The agent deviated from the original task of navigating to http://localhost:3000, logging in, and completing part1 and part2. Instead, it focused on exploring GitHub pages. | Step 10: Navigated to GitHub Copilot page instead of returning to the original task. | Implement a task adherence check to ensure the agent prioritizes the original task over exploratory actions. |
| **B** | The plan expanded excessively, including unrelated steps like exploring GitHub features, which are not part of the original task. | Step 12: Plan included steps to explore GitHub Actions, Codespaces, etc., unrelated to the original task. | Add a plan validation step to prune actions not aligned with the original task. |
| **C** | The agent navigated to external domains (GitHub) despite the "stay on site" rule. | Step 10: URL changed to https://github.com/features/copilot. | Enforce domain checks to prevent navigation away from the target site (http://localhost:3000). |
| **F** | Self-evaluations were unclear, often stating "Unknown" or not assessing action success. | Step 3: Evaluation of clicking the 'Open Sidenav' button was "Unknown". | Enhance evaluation logic to provide clear success/failure assessments based on observable changes. |
| **H** | The agent exceeded the step limit (20 steps) without completing the original task. | Log shows premature shutdown at step 13 without completing part1 or part2. | Implement a step counter with a threshold to trigger task reassessment if the original goal isn't met. |

**Note:** Dimensions D, E, and G were not clearly violated in the provided log. The table focuses on the most impactful issues affecting task success.
"""

def read_data(dir: Path) -> dict[str, str]:
    """
    Reads all log files in the given directory into a dictionary.
    
    Args:
        dir: Path to directory containing log files
        
    Returns:
        Dictionary mapping filename to file contents
    """
    logs = {}
    for file in dir.glob("*.log"):
        with open(file, "r", encoding="utf-8") as f:
            logs[file.name] = f.read()
    return logs


if __name__ == "__main__":
    logs = read_data(DATA_DIR)

    FILENAME = "failed_went_to_github.log"
    LOG_FILE = logs[FILENAME]
    
    RUBRIC = """
1 · Preparation
Locate the ground-truth task.
Read only the earliest system- or human-facing description of the assignment (e.g., "Dismiss popup, login, add item…") and write it down for yourself.
Skim the entire log once to understand the path the agent actually took.
2 · Evaluation dimensions
Check the run against each dimension below. Flag a dimension only if you see a clear violation; ignore it otherwise.

#	Dimension	Typical red flags
A	Task adherence / goal alignment	Agent pursues steps unrelated to the original task; changes domain; never finishes mandatory subtasks.
B	Plan quality & duplication	Plan explodes in length, repeats identical steps, or executes obvious no-ops.
C	Navigation safety	Click leads off the target domain despite a "stay on site" rule.
D	Context & memory management	MESSAGE_LEN or token count grows monotonically; agent stores raw transcripts instead of summaries.
E	Element-selection robustness	Uses stale numeric indices; clicks the wrong control after DOM changes.
F	Progress evaluation clarity	Self-evaluations are always "Unknown" or merely restate the action without judging success.
G	I/O efficiency	Flood of useless HTTP requests (e.g., image sprites, analytics) triggered by drifting to heavy external sites.
H	Stopping criteria / runtime	Step counter, time budget, or retry limit exceeded without detecting futility.
3 · Collect evidence
For every flagged dimension, copy one short snippet (timestamp, step number, URL, or message) that proves the problem.
Keep evidence ≤ 120 characters; trim unrelated text with ellipses.

4 · Generate fixes
Propose one actionable remedy per problem (algorithm change, guard-rail, or heuristic).
Avoid vague advice ("be smarter"); give concrete levers (e.g., "reject actions whose host ≠ localhost").

5 · Output format
Return exactly one Markdown table with four columns in this order:

| Dimension | What went wrong | Evidence | Suggested fix |

Additional rules:

List max 8 rows; prioritise by impact on task success.
Do not add any prose before or after the table.
Use sentence-case, no emojis.
Do not exceed 30 words in any single cell.
6 · Quality checklist (before you send)
✔ Evidence cites step numbers or URLs, not generic phrases.
✔ Every fix is concrete and testable.
✔ No dimension is duplicated.
✔ Table renders in GitHub-flavoured Markdown.
Follow these instructions precisely; any deviation will be treated as rubric non-compliance.
    """

    LOG_CRITIC_PROMPT = """
You are given the following log generated by a web browsing agent attempting to complete a task by
following a plan. Provide some critiques of this agent. Use the following rubric to evaluate the log:

<rubric>
{rubric}
</rubric>

Here is the agent log:
{agent_log}

For each critique, make sure to reference examples from the log, by explicitly referencing the LOG_IDX:
Example: 
[7]: custom_agent.py:274 - Agent did something bad :(
[8]: custom_agent.py:277 - Agent did something worse
...
[12]: custom_agent.py:280 - Agent did something bad again!

Critique:
The agent did something bad:
Reference lines: [7,8,12]

Here is the rubric again
    """

    LOG_CRITIC_PROMPT = """
You are given the following log generated by a web browsing agent attempting to complete a task by
following a plan. Provide some critiques of this agent. Use the following rubric to evaluate the log:

<rubric>
{rubric}
</rubric>

Here is the agent log:
{agent_log}

For each critique, make sure to reference examples from the log, by explicitly referencing the LOG_IDX:
Example: 
[7]: custom_agent.py:274 - Agent did something bad :(
[8]: custom_agent.py:277 - Agent did something worse
...
[12]: custom_agent.py:280 - Agent did something bad again!

Critique:
The agent did something bad:
Reference lines: [7,8,12]

Here is the rubric again
    """

    LOG_AGGREGATOR_PROMPT = """
Here are some critics of a web browsing agent's trajectory log
{critics}

Here is the log that the agent was trying to complete:
{agent_log}

Can you aggregate these critics into a single, more comprehensive critique?
Prune inconsistent critiques and rank them by the most important to pay attention to
Also make sure to include references to the log lines that prompted the critique in your aggregated critique

Now give your output
"""
    llm = ChatCohere(
        model="north-reasoning-alpha", #"command-r7b-12-2024" #"command-r-plus-08-2024",
        model_kwargs={
            'thinking': {
                'type': 'enabled'
            },
        }
    )

    # Process each log file
    collected_results = []
    for i in range(5):
        print(f"\nProcessing {FILENAME}...")
        prompt = LOG_CRITIC_PROMPT.format(rubric=RUBRIC, agent_log=LOG_FILE)
        response = llm.invoke(prompt)
        print(f"\nResults for {FILENAME}:")
        print(response.content)
        collected_results.append(response.content)

    collected_results = "\n".join(collected_results)
    prompt = LOG_AGGREGATOR_PROMPT.format(critics=TEST_AGGREGATOR, agent_log=LOG_FILE)

    print(prompt)

    # response = llm.invoke(prompt)
    # print(response.content)