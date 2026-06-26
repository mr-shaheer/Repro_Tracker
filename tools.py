import re
from agents import function_tool

@function_tool
def parse_bug_report(report_text: str) -> dict:
    """Extract structured info and URL from a freeform bug report."""
    lines = report_text.strip().splitlines()
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, report_text)
    return {
        "title": lines[0] if lines else "Untitled",
        "repro_url": match.group(0) if match else "",
        "steps_to_reproduce": [l for l in lines if l.strip() and not l.startswith(("#", ">"))],
        "expected_behavior": "see report",
        "actual_behavior": "see report",
        "environment": "unknown",
        "severity": "medium",
    }

@function_tool
def search_known_issues(title: str, environment: str) -> str:
    """Search the known issues database for a match."""
    return "No known issues found matching your description."