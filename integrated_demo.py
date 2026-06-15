"""
integrated_demo.py — AgentFileSystem + StateManager working together.

Run directly:
    python integrated_demo.py

WHAT THIS SHOWS
---------------
A mini simulation of BossAgent spawning 3 DeanAgents:

1. Each DeanAgent is REGISTERED in StateManager (state=IDLE)
2. As each Dean starts work -> state=PROCESSING (we print a snapshot here,
   so you see agents mid-flight in different states)
3. Each Dean writes its own report file via AgentFileSystem.write()
   (safe per-file locking)
4. Each Dean also appends a line to a SHARED log file
   (safe concurrent append via the same lock mechanism)
5. After writing, state -> DONE, and the file path is recorded
   in StateManager via add_output_file()
6. BossAgent calls wait_for_all() to block until all Deans are DONE
7. FINAL STEP: print the full agent snapshot (state of every agent)
   AND the file tree (get_tree()) -- this is exactly what Member 4's
   UI would show: agent tree (from StateManager) + file tree (from
   AgentFileSystem), refreshed every couple seconds.
"""

import asyncio
import json
from pathlib import Path

# Import the two classes from the previous files.
# (Make sure filesystem.py and state_manager.py are in the same folder.)
from filesystem import AgentFileSystem
from state_manager import StateManager, AgentState


# ---------------------------------------------------------------------------
# ONE DEAN AGENT'S WORKFLOW
# ---------------------------------------------------------------------------

async def dean_agent(
    name: str,
    work_seconds: float,
    fs: AgentFileSystem,
    sm: StateManager,
    shared_log_path: str,
):
    """
    Simulates one DeanAgent's full lifecycle:
    register -> processing -> do work -> write file -> log -> done
    """

    # 1. Register with StateManager (starts as IDLE)
    await sm.register(name=name, role="DeanAgent", depth=2, parent="BossAgent")

    # 2. Move to PROCESSING and record what it's doing
    await sm.set_state(name, AgentState.PROCESSING, task=f"Designing {name} report")

    # --- simulate the agent "thinking" (e.g. waiting on an LLM call) ---
    await asyncio.sleep(work_seconds)

    # 3. Write its own report file (safe: each agent writes to its own
    #    folder/file, so no lock contention here)
    report_path = await fs.write(
        agent_name=name,
        filename="report.md",
        content=f"# {name} Report\n\nCompleted in {work_seconds}s.\n",
    )

    # 4. Append a line to the SHARED log file.
    #    Multiple Deans append here -> AgentFileSystem's per-file lock
    #    makes sure these lines don't overwrite each other.
    await fs.append(shared_log_path, f"[{name}] finished -> {report_path}\n")

    # 5. Record the output file + mark DONE
    await sm.add_output_file(name, report_path)
    await sm.set_state(name, AgentState.DONE)


# ---------------------------------------------------------------------------
# BOSS AGENT WORKFLOW
# ---------------------------------------------------------------------------

async def boss_agent(fs: AgentFileSystem, sm: StateManager):
    dean_names = ["AcademicDean", "FinanceDean", "ComplianceDean"]

    # Register BossAgent itself
    await sm.register(name="BossAgent", role="BossAgent", depth=3)
    await sm.set_state("BossAgent", AgentState.PROCESSING, task="Spawning deans")

    # Prepare a shared log file all Deans will append to
    shared_log_path = await fs.write(
        agent_name="BossAgent",
        filename="activity_log.md",
        content="# Activity Log\n",
    )

    # ---- Launch all Deans in parallel, but stagger their "work time"
    # so we can catch a mid-run snapshot where some are DONE and
    # some are still PROCESSING.
    work_times = {"AcademicDean": 0.6, "FinanceDean": 1.2, "ComplianceDean": 0.3}

    dean_tasks = [
        asyncio.create_task(
            dean_agent(name, work_times[name], fs, sm, shared_log_path)
        )
        for name in dean_names
    ]

    # ---- MID-RUN SNAPSHOT ----
    # Wait a little, then print the agent states while some Deans are
    # still working. This is what Member 4's UI would poll every 2s.
    await asyncio.sleep(0.4)
    print("\n--- MID-RUN SNAPSHOT (some agents still processing) ---")
    print(json.dumps(sm.snapshot(), indent=2))

    # ---- Wait for everything to finish ----
    await asyncio.gather(*dean_tasks)

    # BossAgent blocks here until all Deans report DONE
    print("\nBossAgent: waiting for all deans via wait_for_all()...")
    all_done = await sm.wait_for_all(dean_names, poll_interval=0.1, timeout=5.0)
    print(f"BossAgent: all_done = {all_done}")

    # Boss writes its final aggregate report referencing each Dean's file
    snapshot = sm.snapshot()
    final_lines = ["# FINAL_LAUNCH_REPORT\n"]
    for dean in dean_names:
        files = snapshot[dean]["files"]
        final_lines.append(f"- {dean}: {files[0]}")
    final_report = await fs.write(
        agent_name="BossAgent",
        filename="FINAL_LAUNCH_REPORT.md",
        content="\n".join(final_lines) + "\n",
    )
    await sm.add_output_file("BossAgent", final_report)
    await sm.set_state("BossAgent", AgentState.DONE, task="Final report written")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

async def main():
    # Fresh output folder each run
    fs = AgentFileSystem(root_dir="integrated_outputs")
    fs.clear()

    sm = StateManager()

    await boss_agent(fs, sm)

    # ---- FINAL SNAPSHOT: full agent states ----
    print("\n=== FINAL AGENT SNAPSHOT (StateManager) ===")
    print(json.dumps(sm.snapshot(), indent=2))

    # Read back the shared log to prove no lines were lost
    shared_log = str(Path("integrated_outputs") / "BossAgent" / "activity_log.md")
    print("\n=== SHARED ACTIVITY LOG (AgentFileSystem, no lost writes) ===")
    print(await fs.read(shared_log))

    # ---- FINAL: directory tree ----
    print("=== FINAL FILE TREE (AgentFileSystem.get_tree()) ===")
    print(fs.get_tree())


if __name__ == "__main__":
    asyncio.run(main())
