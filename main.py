from dataclasses import dataclass
from enum import Enum
from collections import deque

class Agent:

    def __init__(self, name):
        self.name = name
        self.memory = Memory()
        self.queue = Queue()
      
    def process(self, task):
      self.memory.add(task.description)
      task.status = TaskStatus.RUNNING
      print(f"{self.name} processing {task}")
      task.status = TaskStatus.COMPLETED

    def send_message(self, receiver, message):
      receiver.queue.enqueue(message)

    def process_queue(self):
      while not self.queue.is_empty():
          item = self.queue.dequeue()
          self.process(item)
    
    def __repr__(self):
        return f"Agent(name={self.name})"

class TaskStatus(Enum):

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"

class Memory:

    def __init__(self):
        self.history = []

    def add(self, item):
        self.history.append(item)

    def get_all(self):
        return self.history

@dataclass # dataclass is just to make this class short and easier and we donot need to initialize instance variables and representations....
class Task:

    description: str
    status: TaskStatus = TaskStatus.PENDING

@dataclass
class Message:

    sender: str
    receiver: str
    content: str

class PlannerAgent(Agent):

    def process(self, task):
        print(f"{self.name} planning {task.description}")


class WorkerAgent(Agent):

    def process(self, task):
        print(f"{self.name} executing {task.description}")


class AgentFactory:

    @staticmethod # method in class becomes like a normal function.....since it does nto use any instance or class variables
    def create_agent(agent_type, name):
        if agent_type == "planner":
            return PlannerAgent(name)
        elif agent_type == "worker":
            return WorkerAgent(name)
        else:
            raise ValueError("Unknown agent type")


@dataclass
class Event:

    event_type: str
    source: str
    payload: dict


class Queue:

    def __init__(self):
        self.items = deque()

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if self.items:
            return self.items.popleft()

    def is_empty(self):
        return len(self.items) == 0
