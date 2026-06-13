class Planner:

    def __init__(self, llm):
        self.llm = llm

    async def create_plan(self,task,role,sop,memory,rag):

        if "complex" in task.lower():
            return {
                "action": "DELEGATE",

                "agents": [

                    {
                        "role": "Researcher",
                        "sop": "Gather information",
                        "task": "Research topic"
                    },

                    {
                        "role": "Analyst",
                        "sop": "Analyze findings",
                        "task": "Analyze findings"
                    },

                    {
                        "role": "Verifier",
                        "sop": "Verify correctness",
                        "task": "Verify conclusions"
                    }
                ]
            }

        return {
            "action": "COMPLETE"
        }