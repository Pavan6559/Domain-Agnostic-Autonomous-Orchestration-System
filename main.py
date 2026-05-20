import asyncio
from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


@dataclass
class Task:

    description: str
    status: TaskStatus = TaskStatus.PENDING


@dataclass
class Message:

    sender: str
    receiver: str
    content: str


@dataclass
class Event:

    event_type: str
    source: str
    payload: dict


class Memory:

    def __init__(self):
        self.history = []

    def add(self, item):
        self.history.append(item)

    def get_all(self):
        return self.history


class Queue:

    def __init__(self):
        self.items = asyncio.Queue()

    async def enqueue(self, item):
        await self.items.put(item)

    async def dequeue(self):
        return await self.items.get()

    def is_empty(self):
        return self.items.empty()


class Agent:

    def __init__(self, name):

        self.name = name
        self.memory = Memory()
        self.queue = Queue()

    async def process(self, task):

        self.memory.add(task.description)
        task.status = TaskStatus.RUNNING
        print(f"{self.name} processing {task.description}")
        await asyncio.sleep(2)
        task.status = TaskStatus.COMPLETED
        print(f"{self.name} completed {task.description}")

    async def send_message(self, receiver, message):

        await receiver.queue.enqueue(message)

    async def process_queue(self):

        while True:
            item = await self.queue.dequeue()
            await self.process(item)

    def __repr__(self):

        return f"Agent(name={self.name})"


class AgentNode(Agent):

    def __init__(self, name, role, sop=""):

        super().__init__(name)
        self.role = role
        self.sop = sop

    async def process(self, task):

        self.memory.add(task.description)
        task.status = TaskStatus.RUNNING

        print(f"\n[{self.name}]")
        print(f"Role: {self.role}")
        print(f"Task: {task.description}")

        await asyncio.sleep(2)
        task.status = TaskStatus.COMPLETED
        print(f"{self.name} completed task")


class AgentFactory:

    @staticmethod
    def create_agent(name, role, sop=""):

        return AgentNode(
            name=name,
            role=role,
            sop=sop
        )


class BossAgent(Agent):

    def __init__(self, name):

        super().__init__(name)

        self.children = []
        self.task_registry = {}
        self.event_log = []

    async def process(self, task):
        # process method for boss agent will be different from rest of the agents - it will handle task decomposition and agent spawning
        print(f"\n{self.name} received main task:")
        print(task.description)
        domains = self.decompose_task(task)
        await self.spawn_agents(domains)

    def decompose_task(self, task):
    # yet to change this to dynamic decomposition based on task description
    # currently hardcoded for the B.Tech AI degree program example
    # should return something like:
        # return [
        #     {
        #         "name": "AcademicNode",
        #         "role": "Curriculum Planning",
        #         "sop": "Design curriculum and course structure"
        #     },
        #     {
        #         "name": "FinanceNode",
        #         "role": "Finance Planning",
        #         "sop": "Design budget and fee structure"
        #     },
        #     {
        #         "name": "ComplianceNode",
        #         "role": "Compliance Planning",
        #         "sop": "Handle accreditation and compliance"
        #     }
        # ]
        return [
            {
                "name": "AcademicNode",
                "role": "Curriculum Planning",
                "sop": "Design curriculum and course structure"
            },
            {
                "name": "FinanceNode",
                "role": "Finance Planning",
                "sop": "Design budget and fee structure"
            },
            {
                "name": "ComplianceNode",
                "role": "Compliance Planning",
                "sop": "Handle accreditation and compliance"
            }
        ]

    async def spawn_agents(self, domains):

        for domain in domains:

            agent = AgentFactory.create_agent(
                name=domain["name"],
                role=domain["role"],
                sop=domain["sop"]
            )

            self.children.append(agent)

            asyncio.create_task(agent.process_queue())

            subtask = Task(
                description=f"Handle {domain['role']}"
            )

            await agent.queue.enqueue(subtask)

            print(f"{self.name} spawned {agent.name}")


async def main():

    boss = BossAgent("BossAgent")
    asyncio.create_task(boss.process_queue())
    initial_task = Task(
        description="Create B.Tech AI degree program"
    )

    await boss.queue.enqueue(initial_task)

    while True:
        await asyncio.sleep(1)


asyncio.run(main())