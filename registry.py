from core import AgentState


class AgentRegistry:

    def __init__(self):
        self.agents = {}

    def get_idle_agents(self):

        return [
            agent
            for agent in self.agents.values()
            if agent.state == AgentState.IDLE
        ]

    def register(self, agent):
        self.agents[agent.name] = agent

    def get(self, name):
        return self.agents.get(name)

    def get_all(self):
        return list(self.agents.values())