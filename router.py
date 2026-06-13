class EventRouter:

    def __init__(self):
        self.agents = {}

    def register_agent(self, agent):
        self.agents[agent.name] = agent

    async def route_event(self, event):

        receiver = self.agents.get(event.receiver)
        if receiver:
            await receiver.inbox.put(event)
            sender = self.agents.get(event.sender)
            if (
                sender
                and receiver
                and not sender.can_communicate(receiver)
            ):

                print(
                    f"Communication blocked:"
                    f" {sender.name} -> {receiver.name}"
                )

                return
        else:
            print(
                f"[Router] Unknown receiver: "
                f"{event.receiver}"
            )