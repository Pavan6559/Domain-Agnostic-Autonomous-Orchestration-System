from core import (Plan,AgentSpec)

class Planner:

    def __init__(self, llm):
        self.llm = llm

    async def create_plan(self,task,role,sop,memory,rag):
        context = {
        "role": role,
        "sop": sop,
        "task": task,
        "memory": memory,
        "rag": rag
        }

        print("\n===== PLANNER CONTEXT =====")
        print(context)
        if len(task.split()) > 5: # if the task is complex, delegate to multiple agents
            return Plan(
                action="DELEGATE",

                agents=[

                    AgentSpec(
                        role="Researcher",
                        sop="Gather information",
                        task="Research topic"
                    ),

                    AgentSpec(
                        role="Analyst",
                        sop="Analyze findings",
                        task="Analyze findings"
                    ),

                    AgentSpec(
                        role="Verifier",
                        sop="Verify correctness",
                        task="Verify conclusions"
                    )
                ]
            )

        return Plan(
            action="COMPLETE",
            agents=[]
        )