import asyncio

from core import (
    Task,
    TaskStatus,
    Event,
    EventType
)

from runtime import Memory
from registry import AgentRegistry
from router import *


class Agent:

    def __init__(self, name):

        self.name = name
        self.memory = Memory()
        self.inbox = asyncio.Queue()
        self.router = None

    def set_router(self, router):
        self.router = router

    async def send_event(
        self,
        receiver,
        event_type,
        content
    ):

        event = Event(
            sender=self.name,
            receiver=receiver,
            event_type=event_type,
            content=content
        )

        await self.router.route_event(event)

    async def process(self, task):
        self.memory.add(task.description)
        task.status = TaskStatus.RUNNING
        print(
            f"{self.name} processing "
            f"{task.description}"
        )
        await asyncio.sleep(2)
        task.status = TaskStatus.COMPLETED
        print(
            f"{self.name} completed "
            f"{task.description}"
        )

    async def process_event(self, event):
        pass

    async def run(self):
        while True:
            event = await self.inbox.get()
            await self.process_event(event)


class AgentNode(Agent):

    def __init__(self,name,role,sop=""):
        super().__init__(name)
        self.role = role
        self.sop = sop

    async def process_event(self, event):

        if event.event_type == EventType.TASK:

            task = event.content

            self.memory.add(task.description)

            task.status = TaskStatus.RUNNING

            print(f"\n[{self.name}]")
            print(f"Role: {self.role}")
            print(f"Task: {task.description}")

            await asyncio.sleep(2)

            task.status = TaskStatus.COMPLETED

            print(
                f"{self.name} completed task"
            )

            await self.send_event(
                receiver="BossAgent",
                event_type=EventType.STATUS,
                content=f"{self.name} completed"
            )


class AgentFactory:

    @staticmethod
    def create_agent(name,role,sop=""):

        return AgentNode(
            name=name,
            role=role,
            sop=sop
        )


class BossAgent(Agent):

    def __init__(self, name):
        super().__init__(name)
        self.registry = AgentRegistry()
        self.event_log = []

    async def process_event(self, event):

        print(
            f"[Boss] Received "
            f"{event.content}"
        )

    async def start_workflow(self, task):
        print(
            f"\n{self.name} received:"
        )
        print(task.description)
        domains = self.decompose_task(task)
        await self.spawn_agents(domains)

    def decompose_task(self, task):

        return [
            {
                "name": "AcademicNode",
                "role": "Curriculum Planning",
                "sop": "Design curriculum"
            },
            {
                "name": "FinanceNode",
                "role": "Finance Planning",
                "sop": "Budget planning"
            },
            {
                "name": "ComplianceNode",
                "role": "Compliance Planning",
                "sop": "Accreditation"
            }
        ]

    async def spawn_agents(self, domains):

        for domain in domains:

            agent = AgentFactory.create_agent(
                name=domain["name"],
                role=domain["role"],
                sop=domain["sop"]
            )

            self.registry.register(agent)
            agent.set_router(self.router)
            self.router.register_agent(agent)

            asyncio.create_task(
                agent.run()
            )

            subtask = Task(
                description=
                f"Handle {domain['role']}"
            )

            await self.send_event(
                receiver=agent.name,
                event_type=EventType.TASK,
                content=subtask
            )

            print(
                f"{self.name} spawned "
                f"{agent.name}"
            )