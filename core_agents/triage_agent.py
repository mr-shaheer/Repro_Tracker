from agents import Agent
from tools import parse_bug_report
from .repro_agent import repro_agent
from guardrail import BlockPromptInjection

from model import TRIAGE_MODEL

TRIAGE_MAX_TURNS = 6

triage_agent = Agent(
    name = "Triage",
    instructions = """You are the **Triage Agent** for a bug reproduction system.

    ## Core behavior
    - **If user reports a bug** (steps, error, environment): parse it with `parse_bug_report`, then hand off to `ReproductionSpecialist`.
    - **For general chat** (greetings, simple questions): answer directly in 1-2 sentences. Do not refuse or hand off.

    ## Rules
    - Never refuse a greeting or conversational turn.
    - Use handoffs only when the task truly needs a specialist.
    """,
    tools = [parse_bug_report],
    handoffs = [repro_agent],
    input_guardrails = [ BlockPromptInjection],
    model = TRIAGE_MODEL,
)