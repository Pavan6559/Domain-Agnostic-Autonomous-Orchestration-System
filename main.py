import asyncio

from core import Task
from agents import BossAgent


async def main():

    boss = BossAgent("BossAgent")

    asyncio.create_task(
        boss.process_queue()
    )

    initial_task = Task(
        description="Create B.Tech AI degree program"
    )

    await boss.queue.enqueue(initial_task)

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":

    asyncio.run(main())