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
        self.shared_memory = None
        self.state_manager = None
        self.router = None
        self.state = AgentState.IDLE
        self.parent = None
        self.children = []
        self.planner = None
        self.level = 0

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
        await asyncio.sleep(2) # later this will be replaced by try/except block to handle errors and retries
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
    
    def is_sibling(self, agent):
        if self.parent is None:
            return False

        return agent in self.parent.children
    
    def can_communicate(self, target):
        if target == self.parent:
            return True
        if target in self.children:
            return True
        if self.is_sibling(target):
            return True

        return False


class AgentNode(Agent):

    def __init__(self,name,role,sop=""):
        super().__init__(name)
        self.role = role
        self.sop = sop
        self.registry = None
        self.pending_results = []
        self.expected_results = 0
        self.state_manager = None
        self.shared_memory = None
        self.llm = None
        self.prompt_builder = None

    def describe(self):

        return {
            "name": self.name,
            "role": self.role,
            "sop": self.sop
        }

    async def process_event(self, event):

        if event.event_type == EventType.TASK:

            task = event.content
            prompt = self.prompt_builder.build(
                role=self.role,
                sop=self.sop,
                task=task.description,
                memory=self.memory.get_all(),
                rag=""
            )

            decision = await self.planner.create_plan(
                task=task.description,
                role=self.role,
                sop=self.sop,
                memory=self.memory.get_all(),
                rag=""
            )
            agents = decision["agents"]
            action = decision["action"]
            subtasks = decision.get("subtasks",[])
            roles = decision.get("roles",[])

            print(
                f"{self.name} decision:"
                f" {decision}"
            )
            if (action == "DELEGATE" and self.level < 2):
                print(
                    f"{self.name} delegating task"
                )
                self.state = AgentState.WAITING
                print(
                    f"{self.name} waiting for child result"
                )

                self.expected_results = decision["children"]

                for i, (role, subtask) in enumerate(zip(roles, subtasks)):
                    child = await self.spawn_child_agent(
                        name=f"{self.name}_child_{i}",
                        role=role,
                        sop=f"perform {role} work"
                    )
                    print(
                        f"{self.name} spawned "
                        f"{child.name}"
                    )
                    await self.delegate_task(
                        child,
                        Task(
                            description=subtask,
                            owner=self.name
                        )
                    )
            else:
                # process normally
                self.memory.add(task.description)
                context = self.memory.get_all()
                self.state = AgentState.WORKING
                task.status = TaskStatus.RUNNING

                if self.state_manager:
                    self.state_manager.set_state(
                        self.name,
                        AgentState.WORKING
                    )

                print(f"\n[{self.name}]")
                print(f"Role: {self.role}")
                print(f"Task: {task.description}")

                await asyncio.sleep(2)

                self.state = AgentState.IDLE
                task.status = TaskStatus.COMPLETED
                if self.state_manager:
                    self.state_manager.set_state(
                        self.name,
                        AgentState.IDLE
                    )

                print(
                    f"{self.name} completed task"
                )
                self.shared_memory.write(
                    f"{self.name}_result",
                    {
                        "agent": self.name,
                        "task": task.description,
                        "role": self.role
                    }
                )

                if self.parent:
                    await self.send_event(
                        receiver=self.parent.name,
                        event_type=EventType.RESULT,
                        content={
                            "agent": self.name,
                            "role": self.role,
                            "result": f"Completed: {task.description}"
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
            if len(self.pending_results) == self.expected_results:
                final_result = self.aggregate_results()
                self.pending_results.clear()
                self.expected_results = 0
                self.state = AgentState.IDLE
                if self.state_manager:
                    self.state_manager.set_state(
                        self.name,
                        AgentState.IDLE
                    )
                print(
                    f"{self.name} received all expected results"
                )
                # this is just for debugging
                print(
                    final_result
                )
                if self.parent:
                    await self.send_event(
                        receiver=self.parent.name,
                        event_type=EventType.RESULT,
                        content={
                            "agent": self.name,
                            "result": final_result
                        }
                    )
                else:
                    await self.send_event(
                        receiver="BossAgent",
                        event_type=EventType.RESULT,
                        content={
                            "agent": self.name,
                            "result": final_result
                        }
                    )



    async def spawn_child_agent(self,name,role,sop):

        agent = AgentFactory.create_agent(
            name=name,
            role=role,
            sop=sop
        )
        agent.shared_memory = self.shared_memory
        agent.level = self.level+1
        agent.registry = self.registry
        agent.llm = self.llm
        agent.planner = self.planner
        agent.prompt_builder = self.prompt_builder
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

        report = []
        for result in self.pending_results:
            agent_name = result["agent"]
            memory_item = self.shared_memory.read(f"{agent_name}_result")
            report.append(str(memory_item))

        return "\n".join(report)


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
        self.final_results = []

    async def process_event(self, event):

        if event.event_type == EventType.RESULT:
            self.final_results.append(event.content)
            print("\n===== FINAL RESULT =====")
            print(event.content)
        else:
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
            agent.shared_memory = self.shared_memory
            agent.registry = self.registry
            agent.llm = self.llm
            agent.planner = self.planner
            agent.prompt_builder = self.prompt_builder
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

