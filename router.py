class EventRouter:

    def __init__(self):
        self.agents = {}

    def register_agent(self, agent):
        self.agents[agent.name] = agent

    async def route_event(self, event):

        receiver = self.agents.get(event.receiver)
        if receiver:
            await receiver.inbox.put(event)
        else:
            print(
                f"[Router] Unknown receiver: "
                f"{event.receiver}"
            )