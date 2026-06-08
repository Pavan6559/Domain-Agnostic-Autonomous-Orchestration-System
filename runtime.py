import asyncio


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