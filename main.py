import asyncio

from core import Task
from agents import BossAgent
from router import EventRouter


async def main():

    router = EventRouter()

    boss = BossAgent(
        "BossAgent"
    )

    boss.set_router(router)

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