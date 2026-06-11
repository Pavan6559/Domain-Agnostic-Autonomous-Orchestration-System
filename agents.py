import asyncio

from core import (
    AgentState,
    Task,
    TaskStatus,
    Event,
    EventType
)
from scheduler import Scheduler
from runtime import Memory
from registry import AgentRegistry
from router import EventRouter


class Agent:

    def __init__(self, name):

        self.name = name
        self.memory = Memory()
        self.inbox = asyncio.Queue()
        self.router = None
        self.state = AgentState.IDLE
        self.parent = None
        self.children = []

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

    def set_parent(self, parent):
        self.parent = parent

    def add_child(self, child):
        child.set_parent(self)
        self.children.append(child)

    async def run(self):
        while True:
            event = await self.inbox.get()
            await self.process_event(event)


class AgentNode(Agent):

    def __init__(self,name,role,sop=""):
        super().__init__(name)
        self.role = role
        self.sop = sop
        self.registry = None
        self.pending_results = []
        self.expected_results = 0

    def describe(self):

        return {
            "name": self.name,
            "role": self.role,
            "sop": self.sop
        }

    async def process_event(self, event):

        if event.event_type == EventType.TASK:

            task = event.content
            if "complex" in task.description:
                print(
                    f"{self.name} delegating task"
                )
                self.state = AgentState.WAITING
                print(
                    f"{self.name} waiting for child result"
                )
                child = await self.spawn_child_agent(
                    name=f"{self.name}_child",
                    role="Research Assistant",
                    sop="Handle delegated work"
                )
                self.expected_results += 1
                print(
                    f"{self.name} spawned "
                    f"{child.name}"
                )
                await self.delegate_task(child,Task(description="Simple delegated task"))
            else:
                # process normally
                self.memory.add(task.description)
                context = self.memory.get_all()
                self.state = AgentState.WORKING
                task.status = TaskStatus.RUNNING

                print(f"\n[{self.name}]")
                print(f"Role: {self.role}")
                print(f"Task: {task.description}")

                await asyncio.sleep(2)

                self.state = AgentState.IDLE
                task.status = TaskStatus.COMPLETED

                print(
                    f"{self.name} completed task"
                )

                if self.parent:
                    await self.send_event(
                        receiver=self.parent.name,
                        event_type=EventType.RESULT,
                        content={
                            "agent": self.name,
                            "result": task.description
                        }
                    )
                else:
                    await self.send_event(
                        receiver="BossAgent",
                        event_type=EventType.STATUS,
                        content=f"{self.name} completed"
                    )
        elif event.event_type == EventType.RESULT:
            self.pending_results.append(event.content)
            print(f"{self.name} received result: {event.content}")
            results=self.aggregate_results()
            print(f"{self.name} aggregated {len(results)} results")
            if len(results) >= self.expected_results:
                print(
                    f"{self.name} received all expected results"
                )
                self.state = AgentState.IDLE


    async def spawn_child_agent(self,name,role,sop):

        agent = AgentFactory.create_agent(
            name=name,
            role=role,
            sop=sop
        )
        agent.registry = self.registry
        self.add_child(agent)
        self.registry.register(agent)
        agent.set_router(self.router)
        self.router.register_agent(agent)
        asyncio.create_task(
            agent.run()
        )

        return agent
    
    async def delegate_task(self,child,task):

        await self.send_event(
            receiver=child.name,
            event_type=EventType.TASK,
            content=task
        )

    def aggregate_results(self):

        return self.pending_results


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
        self.scheduler = Scheduler()
        self.children = []

    async def process_event(self, event):

        print(
            f"[Boss] Received "
            f"{event.content}"
        )
        await self.dispatch_tasks()

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
            agent.registry = self.registry
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
            self.add_child(agent)

            self.scheduler.submit_task(subtask)

            print(
                f"{self.name} spawned "
                f"{agent.name}"
            )
        await self.dispatch_tasks()
    

    async def dispatch_tasks(self):

        idle_agents = self.registry.get_idle_agents()

        while idle_agents and self.scheduler.has_tasks():
            task = self.scheduler.get_next_task()
            agent = idle_agents.pop(0)

            await self.send_event(
                receiver=agent.name,
                event_type=EventType.TASK,
                content=task
            )

            print(
                f"[Scheduler] Assigned "
                f"{task.description} -> {agent.name}"
            )

    def add_child(self, child):
        child.set_parent(self)
        self.children.append(child)