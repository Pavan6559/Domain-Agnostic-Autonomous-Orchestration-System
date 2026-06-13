class LLMClient:

    async def generate(self,prompt):
        prompt = prompt.lower()
        if "complex" in prompt:
            return {
                "action": "DELEGATE",
                "children": 3,
                "roles": [
                    "Researcher",
                    "Analyst",
                    "Verifier"
                ],
                "subtasks": [
                    "Research Part",
                    "Analysis Part",
                    "Verification Part"
                ]
            }

        return {
            "action": "COMPLETE"
        }

class PromptBuilder:

    def build(self,role,sop,task,memory,rag):
        return f"""Role:{role}SOP:{sop}Task:{task}Memory:{memory}RAG:{rag}"""