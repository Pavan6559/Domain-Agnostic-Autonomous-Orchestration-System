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