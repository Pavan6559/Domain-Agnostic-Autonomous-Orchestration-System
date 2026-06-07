class AgentRegistry:

    def __init__(self):

        self.agents = {}

    def register(self, agent):

        self.agents[agent.name] = agent

    def get(self, name):

        return self.agents.get(name)

    def get_all(self):

        return list(self.agents.values())