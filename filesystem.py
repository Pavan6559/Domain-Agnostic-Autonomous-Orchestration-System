"""
AgentFileSystem — concurrent-safe file writer for UniOrchestrator agents.

Run this file directly to see a demo:
    python filesystem.py

WHAT THIS DEMONSTRATES
-----------------------
1. WITHOUT a lock: many "agents" writing to the SAME file at the same time
   corrupt / overwrite each other's content (race condition).
2. WITH a per-file asyncio.Lock: writes are serialized per file path, so
   nothing gets lost, while writes to DIFFERENT files still happen in parallel.
3. get_tree() — produces a directory listing string (this is what feeds
   Member 4's UI file explorer panel later).
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Dict, Optional


class AgentFileSystem:
    """
    Thread-safe (within asyncio), async-compatible file system.

    Key idea: every unique file PATH gets its own asyncio.Lock.
    - Two agents writing to the SAME file -> one waits for the other.
    - Two agents writing to DIFFERENT files -> both proceed in parallel.
    """

    def __init__(self, root_dir: str):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)

        # path (str) -> asyncio.Lock
        self._file_locks: Dict[str, asyncio.Lock] = {}

        # protects the _file_locks dict itself from concurrent modification
        self._meta_lock = asyncio.Lock()

    async def _get_file_lock(self, path: str) -> asyncio.Lock:
        """Return the lock for `path`, creating it on first use."""
        async with self._meta_lock:
            if path not in self._file_locks:
                self._file_locks[path] = asyncio.Lock()
            return self._file_locks[path]

    def _safe_name(self, name: str) -> str:
        """Make a string safe to use as a folder/file name."""
        return re.sub(r"[^\w\-]", "_", name)

    def agent_dir(self, agent_name: str, parent: Optional[str] = None) -> Path:
        """Return (and create) the output folder for an agent."""
        if parent:
            path = self.root / self._safe_name(parent) / self._safe_name(agent_name)
        else:
            path = self.root / self._safe_name(agent_name)
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def write(
        self,
        agent_name: str,
        filename: str,
        content: str,
        parent: Optional[str] = None,
    ) -> str:
        """
        Write `content` to <agent_name>/<filename>.
        Acquires a per-file lock so concurrent writers don't clobber each other.
        Returns the absolute path written.
        """
        folder = self.agent_dir(agent_name, parent)
        filepath = str(folder / filename)

        lock = await self._get_file_lock(filepath)
        async with lock:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        return filepath

    async def read(self, filepath: str) -> Optional[str]:
        """Read a file's content. Returns None if it doesn't exist."""
        p = Path(filepath)
        if not p.exists():
            return None
        lock = await self._get_file_lock(filepath)
        async with lock:
            return p.read_text(encoding="utf-8")

    async def append(self, filepath: str, content: str):
        """Safely append text to a file."""
        lock = await self._get_file_lock(filepath)
        async with lock:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(content)

    def list_files(self, agent_name: str) -> list:
        """List all files written by a given agent."""
        folder = self.agent_dir(agent_name)
        return [str(p) for p in folder.rglob("*") if p.is_file()]

    def get_tree(self) -> str:
        """
        Return a tree-view string of every file under root.
        This is what would feed Member 4's live file explorer panel.
        """
        lines = [f"{self.root.name}/"]
        for path in sorted(self.root.rglob("*")):
            rel = path.relative_to(self.root)
            depth = len(rel.parts) - 1
            prefix = "  " * depth
            icon = "[dir]" if path.is_dir() else "[file]"
            lines.append(f"{prefix}{icon} {path.name}")
        return "\n".join(lines)

    def clear(self):
        """Delete everything under root (use to reset between demo runs)."""
        import shutil

        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._file_locks.clear()


# ---------------------------------------------------------------------------
# DEMO / SELF-TEST
# ---------------------------------------------------------------------------

# async def write_no_lock(path: str, agent_id: int, delay: float):
#     """Simulates an UNSAFE write: open, sleep (context switch), then write."""
#     f = open(path, "w")
#     await asyncio.sleep(delay)  # <-- another coroutine can run here
#     f.write(f"Agent-{agent_id} was here\n")
#     f.close()


# async def demo_without_lock():
#     print("\n=== DEMO 1: WITHOUT LOCK (race condition) ===")
#     path = "unsafe_shared.txt"

#     # 5 "agents" all try to write to the same file at once.
#     # Different delays simulate real async work interleaving.
#     await asyncio.gather(
#         write_no_lock(path, 1, 0.05),
#         write_no_lock(path, 2, 0.01),
#         write_no_lock(path, 3, 0.03),
#         write_no_lock(path, 4, 0.02),
#         write_no_lock(path, 5, 0.04),
#     )

#     with open(path) as f:
#         content = f.read()

#     print(f"Final content of {path!r}:")
#     print(content or "(EMPTY — every agent's write got overwritten!)")
#     os.remove(path)


async def demo_with_lock():
    print("\n=== DEMO 2: WITH AgentFileSystem (safe) ===")
    fs = AgentFileSystem(root_dir="demo_outputs")
    fs.clear()

    # 5 agents writing to DIFFERENT files -> all run in parallel, no conflicts
    await asyncio.gather(
        fs.write("AcademicDean", "report.md", "# Academic report\nContent A"),
        fs.write("FinanceDean", "report.md", "# Finance report\nContent B"),
        fs.write("ComplianceDean", "report.md", "# Compliance report\nContent C"),
    )

    # 3 agents writing to the SAME shared file -> serialized by the lock,
    # each call to .write() fully replaces the file, so let's demonstrate
    # safe APPEND instead, which is the realistic "shared log" use case.
    shared_log = str(fs.agent_dir("BossAgent") / "activity_log.md")
    # ensure file exists first
    open(shared_log, "w").close()

    async def log_line(agent_name: str, msg: str):
        await fs.append(shared_log, f"[{agent_name}] {msg}\n")

    await asyncio.gather(
        log_line("AcademicDean", "finished curriculum design"),
        log_line("FinanceDean", "finished fee structure"),
        log_line("ComplianceDean", "finished NBA checklist"),
    )

    print("Shared activity log (all 3 lines preserved):")
    print(await fs.read(shared_log))

    print("\nDirectory tree:")
    print(fs.get_tree())


if __name__ == "__main__":
    # asyncio.run(demo_without_lock())
    asyncio.run(demo_with_lock())
    
