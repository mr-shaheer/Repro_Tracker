import os 
import asyncio
from uuid import uuid4
from dotenv import load_dotenv
from core_agents.triage_agent import triage_agent, TRIAGE_MAX_TURNS
from core_agents.repro_agent import repro_agent, REPRO_MAX_TURNS
from agents.sandbox import SandboxRunConfig
from agents.extensions.sandbox import E2BSandboxClient, E2BSandboxClientOptions, E2BSandboxType
from agents.exceptions import InputGuardrailTripwireTriggered
from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent
from agents import RunResultStreaming, Runner, RunConfig, SQLiteSession, SessionSettings

load_dotenv()
e2b_client = E2BSandboxClient()

def build_run_config(session_id: str, turn_num: int) -> RunConfig:
    return RunConfig(
        workflow_name="Repro Tracker",
        trace_id="trace_" + uuid4().hex,
        trace_metadata={
            "session_id": session_id,
            "turn": str(turn_num),
            "env": "dev",
        },
        tracing_disabled="OPENAI_API_KEY" not in os.environ,
        sandbox=SandboxRunConfig(
            client=e2b_client,
            options=E2BSandboxClientOptions(
                sandbox_type=E2BSandboxType.E2B,
                timeout=900,
            ),
        ),
    )

async def main() -> None:
    active_agent = triage_agent
    print("Your Repro Tracker is Ready. Type /exit to quit")
    session = SQLiteSession( "default-cli", "bugs.db", session_settings = SessionSettings(limit = 16))
    turn = 0

    while True :

        user_input = input("You : ").strip()

        if user_input.lower() == "/exit":
            break
        if not user_input :
            continue

        print("Assistant : ", end = "", flush = True) 

        if active_agent == triage_agent:
            max_turns = TRIAGE_MAX_TURNS
        else :
            max_turns = REPRO_MAX_TURNS


        try :

            result: RunResultStreaming = Runner.run_streamed(
                active_agent,
                user_input,
                session = session,
                max_turns = max_turns,
                run_config = build_run_config(session.session_id, turn )
            )

            async for event in result.stream_events():
                if isinstance(event, RawResponsesStreamEvent):
                    delta: str | None = getattr(event.data, "delta", None)
                    if delta:
                        print(delta, end="", flush=True)
                elif isinstance(event, RunItemStreamEvent):
                    if event.name == "tool_called":
                        tool_name: str = getattr(event.item.raw_item, "name", "?")
                        print(f"\n  [tool: {tool_name}]", end="", flush=True)
                    elif event.name == "handoff":
                        print(f"\n  [handoff]", end="", flush=True)

            await asyncio.sleep(0)

            if result.interruptions:
                state = result.to_state()
                for interruption in result.interruptions:
                    print(f"\n\n--- Approval needed ---")
                    print(f"{interruption}")
                    response = input("Approve? (y/n): ").strip().lower()
                    if response.startswith("y"):
                        state.approve(interruption)
                        print("  [approved]\n")
                    else:
                        state.reject(interruption)
                        print("  [rejected]\n")
                result = await Runner.run_streamed(
                    active_agent,
                    state,
                    session=session,
                    max_turns=max_turns,
                    run_config=build_run_config(session.session_id, turn),
                )
                async for event in result.stream_events():
                    if isinstance(event, RawResponsesStreamEvent):
                        delta: str | None = getattr(event.data, "delta", None)
                        if delta:
                            print(delta, end="", flush=True)
                
                
            active_agent = result.last_agent
            turn += 1
            print("\n")
        
        except InputGuardrailTripwireTriggered :
            print("\nI can only help with bug reproduction, Please provide a valid bug report.")
        except Exception :
            print("\nSever Down!")


if __name__ == "__main__":
    asyncio.run(main())