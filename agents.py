import asyncio

from core import Task, TaskStatus
from runtime import Memory, Queue


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

        print(f"\n{self.name} received main task:")
        print(task.description)

        domains = self.decompose_task(task)

        await self.spawn_agents(domains)

    def decompose_task(self, task):

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