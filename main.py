import asyncio

from core import Task
from agents import BossAgent
from llm import LLMClient, PromptBuilder
from memory import SharedMemory
from planner import Planner
from router import EventRouter


async def main():

    llm = LLMClient()
    prompt_builder = PromptBuilder()
    router = EventRouter()
    shared_memory = SharedMemory()
    planner=Planner(llm)
    boss = BossAgent(
        "BossAgent"
    )
    boss.llm = llm
    boss.planner = planner
    boss.prompt_builder = prompt_builder
    boss.set_router(router)
    boss.shared_memory = shared_memory
    boss.state_manager = None
    router.register_agent(boss)

    asyncio.create_task(
        boss.run()
    )

    initial_task = Task(
        description=
        "Create B.Tech AI degree program"
    )

    await boss.start_workflow(
        initial_task
    )

    while True:

        await asyncio.sleep(1)


if __name__ == "__main__":

    asyncio.run(main())