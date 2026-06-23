from urllib import response

from core import (Plan,AgentSpec)
import json

class Planner:

    def __init__(self, llm):
        self.llm = llm

    def build_prompt(self,task,role,sop,memory,rag):

        return f"""
        You are an orchestration planner.

        Task:
        {task}

        Role:
        {role}

        SOP:
        {sop}

        Memory:
        {memory}

        Context:
        {rag}

        Return ONLY valid JSON.

        Format:

        {{
            "action":"DELEGATE",
            "agents":[
                {{
                    "role":"Researcher",
                    "sop":"Gather information",
                    "task":"Research topic"
                }}
            ]
        }}

        or

        {{
            "action":"COMPLETE",
            "agents":[]
        }}
        """

    def parse_plan(self,response):
        print(
            "\n===== RESPONSE ====="
        )
        print(response)

        data = json.loads(response)
        agents = []

        for spec in data["agents"]:
            agents.append(
                AgentSpec(
                    role=spec["role"],
                    sop=spec["sop"],
                    task=spec["task"]
                )
            )

        return Plan(
            action=data["action"],
            agents=agents
        )


    async def create_plan(self,task,role,sop,memory,rag):
        prompt = self.build_prompt(
            task,
            role,
            sop,
            memory,
             rag
        )

        response = await self.llm.generate(prompt)
        print(
            "\n===== RAW PLAN ====="
        )
        print(response)
        plan = self.parse_plan(response)
        return plan