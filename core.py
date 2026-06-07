from dataclasses import dataclass
from enum import Enum


class TaskStatus(Enum):

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"


class EventType(Enum):

    TASK = "TASK"
    STATUS = "STATUS"


@dataclass
class Task:

    description: str
    status: TaskStatus = TaskStatus.PENDING


@dataclass
class Event:

    sender: str
    receiver: str
    event_type: EventType
    content: object