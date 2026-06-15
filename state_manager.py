"""
StateManager — centralized state store for all agents.

Run this file directly to see a demo:
    python state_manager.py

WHAT THIS DEMONSTRATES
-----------------------
1. AgentState enum: IDLE -> PROCESSING -> DONE / FAILED
2. AgentStatus dataclass: holds everything about one agent
   (role, depth, state, current task, output files, todo list, timestamps)
3. StateManager: a dict of AgentStatus, protected by asyncio.Lock,
   with register / set_state / snapshot
4. wait_for_all(): polling loop that blocks until a set of agents
   reach DONE (or times out) — this is how BossAgent knows when
   all its DeanAgents have finished.
5. snapshot(): a JSON-friendly dict — this is what would be polled
   every 2 seconds by Member 4's Gradio UI.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class AgentState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class AgentStatus:
    name: str
    role: str
    depth: int                 # 3=Boss, 2=Dean, 1=Ops, 0=Leaf
    parent: Optional[str] = None
    state: AgentState = AgentState.IDLE
    task: Optional[str] = None
    output_files: List[str] = field(default_factory=list)
    todo_list: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class StateManager:
    """
    Central registry: name -> AgentStatus.

    BossAgent uses this to know when all its children are done.
    UI uses snapshot() to render the live agent tree.
    """

    def __init__(self):
        self._agents: Dict[str, AgentStatus] = {}
        self._lock = asyncio.Lock()

    async def register(
        self, name: str, role: str, depth: int, parent: Optional[str] = None
    ):
        """Called when an agent is spawned."""
        async with self._lock:
            self._agents[name] = AgentStatus(
                name=name, role=role, depth=depth, parent=parent
            )

    async def set_state(
        self, name: str, state: AgentState, task: Optional[str] = None
    ):
        """Update an agent's state (and optionally its current task)."""
        async with self._lock:
            if name not in self._agents:
                raise KeyError(f"Agent {name!r} not registered")

            agent = self._agents[name]
            agent.state = state
            if task is not None:
                agent.task = task

            if state == AgentState.PROCESSING and agent.started_at is None:
                agent.started_at = datetime.now()
            elif state in (AgentState.DONE, AgentState.FAILED):
                agent.completed_at = datetime.now()

    async def add_output_file(self, agent_name: str, filepath: str):
        async with self._lock:
            self._agents[agent_name].output_files.append(filepath)

    async def update_todo(self, agent_name: str, todo_items: List[str]):
        async with self._lock:
            self._agents[agent_name].todo_list = todo_items

    async def are_all_done(self, names: List[str]) -> bool:
        """True only if every named agent has state == DONE."""
        async with self._lock:
            return all(
                name in self._agents and self._agents[name].state == AgentState.DONE
                for name in names
            )

    async def wait_for_all(
        self, names: List[str], poll_interval: float = 0.2, timeout: float = 30.0
    ) -> bool:
        """
        Block until every agent in `names` is DONE, or until `timeout`
        seconds pass. Returns True if all finished, False on timeout.

        This is a POLLING loop: every `poll_interval` seconds, check the
        state dict. Simple, and good enough for a handful of agents.
        """
        elapsed = 0.0
        while elapsed < timeout:
            if await self.are_all_done(names):
                return True
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        return False

    def snapshot(self) -> Dict:
        """
        Return the whole state as a plain dict — JSON serializable.
        This is what Member 4's UI would poll every 2 seconds.
        """
        return {
            name: {
                "role": s.role,
                "depth": s.depth,
                "state": s.state.value,
                "task": s.task,
                "files": s.output_files,
                "todo": s.todo_list,
                "parent": s.parent,
            }
            for name, s in self._agents.items()
        }


# ---------------------------------------------------------------------------
# DEMO / SELF-TEST
# ---------------------------------------------------------------------------

async def fake_dean_agent(sm: StateManager, name: str, work_seconds: float):
    """Simulates a Dean agent doing some work, then finishing."""
    await sm.register(name=name, role="DeanAgent", depth=2, parent="BossAgent")
    await sm.set_state(name, AgentState.PROCESSING, task=f"Designing {name} report")

    await asyncio.sleep(work_seconds)  # simulate LLM call / work

    await sm.add_output_file(name, f"outputs/{name}/report.md")
    await sm.update_todo(name, ["draft report", "self-review", "finalize"])
    await sm.set_state(name, AgentState.DONE)
    print(f"[{name}] finished after {work_seconds}s")


async def boss_agent(sm: StateManager, dean_names: List[str]):
    """Simulates BossAgent: register self, spawn deans, wait for all."""
    await sm.register(name="BossAgent", role="BossAgent", depth=3)
    await sm.set_state("BossAgent", AgentState.PROCESSING, task="Spawning deans")

    # Spawn all deans in parallel with different work times
    work_times = [0.5, 1.0, 0.3]
    await asyncio.gather(
        *[
            fake_dean_agent(sm, name, t)
            for name, t in zip(dean_names, work_times)
        ]
    )

    print("\nBossAgent: waiting for all deans to be DONE...")
    all_done = await sm.wait_for_all(dean_names, poll_interval=0.1, timeout=5.0)
    print(f"BossAgent: all_done = {all_done}")

    await sm.set_state("BossAgent", AgentState.DONE, task="Final report written")


async def main():
    sm = StateManager()
    dean_names = ["AcademicDean", "FinanceDean", "ComplianceDean"]

    await boss_agent(sm, dean_names)

    print("\n=== FINAL SNAPSHOT (this is what the UI would poll) ===")
    import json
    print(json.dumps(sm.snapshot(), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
